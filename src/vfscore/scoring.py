"""LLM scoring orchestration with repeats."""

# Suppress gRPC warnings before any Google library imports
import os
os.environ["GRPC_VERBOSITY"] = "NONE"  # Must be NONE, not ERROR
os.environ["GRPC_TRACE"] = ""  # Disable all tracing
os.environ["GRPC_PYTHON_LOG_LEVEL"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GOOGLE_LOGGING_VERBOSITY"] = "3"

import getpass
import hashlib
import json
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from rich.console import Console
from rich.progress import track

from vfscore.config import Config
from vfscore.llm.gemini import GeminiClient

console = Console()


def create_batch_directory_name() -> str:
    """Create a timestamped batch directory name with username.

    Format: batch_YYYYMMDD_HHMMSS_user_<username>

    Returns:
        Batch directory name string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        username = getpass.getuser()
    except Exception:
        username = "unknown"

    # Sanitize username (remove special chars that could be problematic in filenames)
    username = "".join(c if c.isalnum() or c in "-_" else "_" for c in username)

    return f"batch_{timestamp}_user_{username}"


def create_batch_metadata(
    model: str,
    repeats: int,
    config: Config,
) -> Dict:
    """Create batch metadata for provenance tracking.

    Args:
        model: Model name used for scoring
        repeats: Number of repeats per item
        config: Configuration object

    Returns:
        Dictionary with batch metadata
    """
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "unknown"

    try:
        username = getpass.getuser()
    except Exception:
        username = "unknown"

    # Create config hash for tracking configuration changes
    config_str = json.dumps({
        "rubric_weights": config.scoring.rubric_weights,
        "temperature": config.scoring.temperature,
        "top_p": config.scoring.top_p,
    }, sort_keys=True)
    config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:8]

    return {
        "timestamp": datetime.now().isoformat(),
        "user": username,
        "hostname": hostname,
        "model": model,
        "repeats": repeats,
        "config_hash": config_hash,
        "rubric_weights": config.scoring.rubric_weights,
        "temperature": config.scoring.temperature,
        "top_p": config.scoring.top_p,
    }


def load_packets(labels_dir: Path) -> List[Dict]:
    """Load all scoring packets."""
    packets = []
    
    for packet_path in labels_dir.glob("*/packet.json"):
        with open(packet_path, "r", encoding="utf-8") as f:
            packet = json.load(f)
            packets.append(packet)
    
    return packets


def get_llm_client(model_name: str, config: Config):
    """Get LLM client instance."""
    # Normalize model name
    model_lower = model_name.lower()
    
    if "gemini" in model_lower:
        # Map common names to actual model IDs
        if "2.5-pro" in model_lower or model_lower == "gemini":
            actual_model = "gemini-2.5-pro"
        elif "2.5-flash" in model_lower:
            actual_model = "gemini-2.5-flash"
        else:
            actual_model = model_name
        
        return GeminiClient(
            model_name=actual_model,
            temperature=config.scoring.temperature,
            top_p=config.scoring.top_p,
        )
    else:
        raise ValueError(f"Unsupported model: {model_name}")


def score_item_with_repeats(
    packet: Dict,
    client,
    rubric_weights: Dict[str, float],
    repeats: int,
    output_dir: Path,
) -> List[Dict]:
    """Score a single item with multiple repeats."""
    
    item_id = packet["item_id"]
    
    # Collect image paths (GT images first, then candidate)
    image_paths = [Path(p) for p in packet["gt_labeled_paths"]]
    image_paths.append(Path(packet["cand_labeled_path"]))
    
    # Context for the LLM
    context = {
        "item_id": item_id,
        "l1": packet["l1"],
        "l2": packet["l2"],
        "l3": packet["l3"],
        "gt_count": packet["gt_count"],
        "gt_labels": packet["gt_labels"],
        "candidate_label": packet["candidate_label"],
    }
    
    # Run repeats
    results = []
    
    for rep_idx in range(1, repeats + 1):
        try:
            result = client.score_visual_fidelity(
                image_paths=image_paths,
                context=context,
                rubric_weights=rubric_weights,
            )
            
            # Save result
            output_path = output_dir / f"rep_{rep_idx}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            results.append(result)
            
        except Exception as e:
            console.print(f"[red]Error scoring {item_id} (repeat {rep_idx}): {e}[/red]")
            # Continue with other repeats
    
    return results


def run_scoring(
    config: Config,
    model: str = "gemini-2.5-pro",
    repeats: int = 3,
) -> None:
    """Run LLM scoring for all items."""

    # Load packets
    labels_dir = config.paths.out_dir / "labels"
    if not labels_dir.exists():
        raise FileNotFoundError(f"Labels directory not found: {labels_dir}")

    packets = load_packets(labels_dir)

    if not packets:
        raise ValueError("No scoring packets found. Run 'vfscore package' first.")

    console.print(f"\n[bold]Scoring {len(packets)} items with {model} ({repeats} repeats each)...[/bold]")

    # Initialize LLM client
    client = get_llm_client(model, config)
    console.print(f"[cyan]Using model: {client.model_name}[/cyan]")

    # Determine base results directory
    if config.scoring.results_dir:
        base_llm_calls_dir = Path(config.scoring.results_dir)
        console.print(f"[cyan]Using shared results directory: {base_llm_calls_dir}[/cyan]")
    else:
        base_llm_calls_dir = config.paths.out_dir / "llm_calls"

    # Create batch directory if batch mode is enabled
    batch_dir_name = None
    batch_metadata = None

    if config.scoring.use_batch_mode:
        batch_dir_name = create_batch_directory_name()
        batch_metadata = create_batch_metadata(model, repeats, config)
        console.print(f"[cyan]Batch mode enabled: {batch_dir_name}[/cyan]")

    # Normalize model name for directory
    model_dir_name = model.replace("gemini-", "").replace("-", "_")
    if not model_dir_name:
        model_dir_name = "gemini"

    # Score each item
    total_calls = 0
    success_items = 0

    for packet in track(packets, description=f"Scoring with {model}"):
        item_id = packet["item_id"]

        # Build output directory path
        if config.scoring.use_batch_mode:
            output_dir = base_llm_calls_dir / model_dir_name / item_id / batch_dir_name
        else:
            # Legacy mode: no batch directory
            output_dir = base_llm_calls_dir / model_dir_name / item_id

        output_dir.mkdir(parents=True, exist_ok=True)

        # Save batch metadata once per item
        if config.scoring.use_batch_mode and batch_metadata:
            batch_info_path = output_dir / "batch_info.json"
            with open(batch_info_path, "w", encoding="utf-8") as f:
                json.dump(batch_metadata, f, indent=2, ensure_ascii=False)

        try:
            results = score_item_with_repeats(
                packet=packet,
                client=client,
                rubric_weights=config.scoring.rubric_weights,
                repeats=repeats,
                output_dir=output_dir,
            )

            if results:
                total_calls += len(results)
                success_items += 1

        except Exception as e:
            console.print(f"[red]Failed to score {item_id}: {e}[/red]")

    console.print(f"[green]Completed {total_calls} API calls for {success_items}/{len(packets)} items[/green]")

    if config.scoring.use_batch_mode:
        console.print(f"[cyan]Results saved in batch: {batch_dir_name}[/cyan]")


if __name__ == "__main__":
    from vfscore.config import get_config
    
    config = get_config()
    run_scoring(config, model="gemini-2.5-pro", repeats=3)
