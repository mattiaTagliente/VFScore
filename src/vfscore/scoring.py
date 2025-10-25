"""LLM scoring orchestration with repeats."""

# Suppress gRPC warnings before any Google library imports
import os
os.environ["GRPC_VERBOSITY"] = "NONE"  # Must be NONE, not ERROR
os.environ["GRPC_TRACE"] = ""  # Disable all tracing
os.environ["GRPC_PYTHON_LOG_LEVEL"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GOOGLE_LOGGING_VERBOSITY"] = "3"

import asyncio
import getpass
import hashlib
import json
import socket
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn

from vfscore.config import Config
from vfscore.llm.gemini import GeminiClient
from vfscore.llm.gemini_async import AsyncGeminiClient
from vfscore.llm.key_pool import GeminiKeyPool, QuotaExhaustedError
from vfscore.llm.cost_tracker import (
    CostEstimator,
    CostTracker,
    display_billing_warning,
    display_cost_estimate,
    check_cost_threshold,
)

console = Console(legacy_windows=True)


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

    # Note: temperature and top_p will be added when calling create_batch_metadata
    # in run_scoring function to use actual values (not just config defaults)
    config_str = json.dumps({
        "rubric_weights": config.scoring.rubric_weights,
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
    }


def load_packets(labels_dir: Path) -> List[Dict]:
    """Load all scoring packets."""
    packets = []

    for packet_path in labels_dir.glob("*/packet.json"):
        with open(packet_path, "r", encoding="utf-8") as f:
            packet = json.load(f)
            packets.append(packet)

    return packets


def is_item_already_scored(output_dir: Path, repeats: int) -> bool:
    """Check if an item has already been scored with the required number of repeats.

    Args:
        output_dir: Output directory where results should be
        repeats: Required number of repeats

    Returns:
        True if all repeat files exist, False otherwise
    """
    if not output_dir.exists():
        return False

    # Check if all repeat files exist
    for rep_idx in range(1, repeats + 1):
        rep_file = output_dir / f"rep_{rep_idx}.json"
        if not rep_file.exists():
            return False

    return True


def count_existing_repeats_with_parameters(
    item_dir: Path,
    temperature: float,
    top_p: float,
    tolerance: float = 0.001
) -> int:
    """Count existing repeats for an item with matching temperature/top_p parameters.

    This function looks across ALL batch directories for the item and counts
    how many repeats exist with matching parameters (within tolerance).

    Args:
        item_dir: Item directory (e.g., outputs/llm_calls/gemini/558736)
        temperature: Target temperature
        top_p: Target top_p
        tolerance: Tolerance for float comparison

    Returns:
        Number of existing repeats with matching parameters
    """
    if not item_dir.exists():
        return 0

    total_repeats = 0

    # Iterate through all batch directories
    for batch_dir in item_dir.iterdir():
        if not batch_dir.is_dir() or not batch_dir.name.startswith("batch_"):
            continue

        # Read batch metadata
        batch_info_path = batch_dir / "batch_info.json"
        if not batch_info_path.exists():
            continue

        try:
            with open(batch_info_path, "r", encoding="utf-8") as f:
                batch_info = json.load(f)

            # Check if temperature and top_p match (within tolerance)
            batch_temp = batch_info.get("temperature", None)
            batch_top_p = batch_info.get("top_p", None)

            if batch_temp is None or batch_top_p is None:
                continue

            if abs(batch_temp - temperature) < tolerance and abs(batch_top_p - top_p) < tolerance:
                # Count rep_*.json files in this batch
                rep_files = list(batch_dir.glob("rep_*.json"))
                total_repeats += len(rep_files)

        except Exception:
            continue

    return total_repeats


def resolve_api_keys(config: Config) -> List[str]:
    """Resolve API keys from config (supports environment variables)."""
    if not config.scoring.api_keys:
        # Fall back to single GEMINI_API_KEY env var
        single_key = os.getenv("GEMINI_API_KEY")
        if not single_key:
            raise ValueError("No API keys configured. Set GEMINI_API_KEY or scoring.api_keys in config")
        return [single_key]

    resolved_keys = []
    for key in config.scoring.api_keys:
        if key.startswith("$"):
            # Environment variable reference
            env_var = key[1:]  # Remove $
            env_value = os.getenv(env_var)
            if not env_value:
                raise ValueError(f"Environment variable {env_var} not set")
            resolved_keys.append(env_value)
        else:
            # Direct API key (not recommended for security)
            resolved_keys.append(key)

    return resolved_keys


def create_key_pool(config: Config) -> Optional[GeminiKeyPool]:
    """Create GeminiKeyPool if multi-key mode is enabled."""
    if not config.scoring.use_async:
        return None

    api_keys = resolve_api_keys(config)

    if len(api_keys) == 1:
        console.print("[cyan]Async mode with single API key[/cyan]")
        return None  # Single key - no need for pool

    # Multi-key mode
    key_labels = config.scoring.key_labels or [f"key_{i+1}" for i in range(len(api_keys))]

    pool = GeminiKeyPool(
        api_keys=api_keys,
        key_labels=key_labels,
        rpm_limit=config.scoring.rpm_limit,
        tpm_limit=config.scoring.tpm_limit,
        rpd_limit=config.scoring.rpd_limit,
    )

    return pool


def get_llm_client(model_name: str, temperature: float, top_p: float, run_id: str = None):
    """Get LLM client instance (synchronous, backward compatibility).

    Args:
        model_name: Model name to use
        temperature: Sampling temperature
        top_p: Top-p sampling parameter
        run_id: Unique run identifier (optional, will be auto-generated if None)
    """
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
            temperature=temperature,
            top_p=top_p,
            run_id=run_id,
        )
    else:
        raise ValueError(f"Unsupported model: {model_name}")


def get_async_llm_client(
    model_name: str,
    temperature: float,
    top_p: float,
    run_id: str,
    key_pool: Optional[GeminiKeyPool] = None,
):
    """Get async LLM client instance.

    Args:
        model_name: Model name to use
        temperature: Sampling temperature
        top_p: Top-p sampling parameter
        run_id: Unique run identifier
        key_pool: Optional GeminiKeyPool for multi-key mode
    """
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

        return AsyncGeminiClient(
            model_name=actual_model,
            temperature=temperature,
            top_p=top_p,
            run_id=run_id,
            key_pool=key_pool,
        )
    else:
        raise ValueError(f"Unsupported model: {model_name}")


def score_item_with_repeats(
    packet: Dict,
    model_name: str,
    temperature: float,
    top_p: float,
    rubric_weights: Dict[str, float],
    repeats: int,
    output_dir: Path,
) -> List[Dict]:
    """Score a single item with multiple repeats (synchronous).

    Each repeat gets a unique run_id for statistical independence.
    """

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
            # Generate unique run_id for each repeat
            run_id = str(uuid.uuid4())

            # Create new client for each repeat with unique run_id
            client = get_llm_client(
                model_name=model_name,
                temperature=temperature,
                top_p=top_p,
                run_id=run_id
            )

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


async def score_item_with_repeats_async(
    packet: Dict,
    model_name: str,
    temperature: float,
    top_p: float,
    rubric_weights: Dict[str, float],
    repeats: int,
    output_dir: Path,
    key_pool: Optional[GeminiKeyPool] = None,
) -> List[Dict]:
    """Score a single item with multiple repeats (asynchronous).

    Each repeat gets a unique run_id for statistical independence.
    Repeats are processed concurrently for speed.
    """

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

    # Create tasks for all repeats
    async def score_one_repeat(rep_idx: int) -> Optional[Dict]:
        try:
            # Generate unique run_id for each repeat
            run_id = str(uuid.uuid4())

            # Create async client for this repeat
            client = get_async_llm_client(
                model_name=model_name,
                temperature=temperature,
                top_p=top_p,
                run_id=run_id,
                key_pool=key_pool,
            )

            result = await client.score_visual_fidelity_async(
                image_paths=image_paths,
                context=context,
                rubric_weights=rubric_weights,
            )

            # Save result
            output_path = output_dir / f"rep_{rep_idx}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            return result

        except Exception as e:
            console.print(f"[red]Error scoring {item_id} (repeat {rep_idx}): {e}[/red]")
            return None

    # Run all repeats concurrently
    tasks = [score_one_repeat(rep_idx) for rep_idx in range(1, repeats + 1)]
    results = await asyncio.gather(*tasks)

    # Filter out None values (failed repeats)
    return [r for r in results if r is not None]


async def run_scoring_async(
    config: Config,
    model: str,
    repeats: int,
    actual_temperature: float,
    actual_top_p: float,
    packets: List[Dict],
    base_llm_calls_dir: Path,
    batch_dir_name: Optional[str],
    batch_metadata: Optional[Dict],
    model_dir_name: str,
    cost_tracker: CostTracker,
) -> Tuple[int, int, int]:
    """Run async scoring for all items with progress tracking and cost monitoring.

    Returns:
        (total_calls, success_items, skipped_items)
    """
    # Create key pool
    key_pool = create_key_pool(config)

    # Track statistics
    total_calls = 0
    success_items = 0
    skipped_items = 0

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"Scoring with {model} (async)", total=len(packets))

        for idx, packet in enumerate(packets, 1):
            item_id = packet["item_id"]
            item_start = time.time()

            # Update progress
            progress.update(task, description=f"Scoring {item_id} ({idx}/{len(packets)})")

            # Build output directory path
            if config.scoring.use_batch_mode:
                output_dir = base_llm_calls_dir / model_dir_name / item_id / batch_dir_name
                item_dir = base_llm_calls_dir / model_dir_name / item_id
            else:
                output_dir = base_llm_calls_dir / model_dir_name / item_id
                item_dir = output_dir

            # Smart skip: Check across all batches for matching parameters
            existing_repeats = count_existing_repeats_with_parameters(
                item_dir, actual_temperature, actual_top_p
            )

            if existing_repeats >= repeats:
                skipped_items += 1
                success_items += 1
                total_calls += repeats
                console.print(f"[dim]  {item_id}: [yellow]skipped[/yellow] (already have {existing_repeats}/{repeats} repeats with temp={actual_temperature}, top_p={actual_top_p})[/dim]")
                progress.advance(task)
                continue
            elif existing_repeats > 0:
                console.print(f"[dim]  {item_id}: Found {existing_repeats}/{repeats} existing repeats, running {repeats - existing_repeats} more...[/dim]")

            output_dir.mkdir(parents=True, exist_ok=True)

            # Save batch metadata
            if config.scoring.use_batch_mode and batch_metadata:
                batch_info_path = output_dir / "batch_info.json"
                with open(batch_info_path, "w", encoding="utf-8") as f:
                    json.dump(batch_metadata, f, indent=2, ensure_ascii=False)

            try:
                results = await score_item_with_repeats_async(
                    packet=packet,
                    model_name=model,
                    temperature=actual_temperature,
                    top_p=actual_top_p,
                    rubric_weights=config.scoring.rubric_weights,
                    repeats=repeats,
                    output_dir=output_dir,
                    key_pool=key_pool,
                )

                if results:
                    total_calls += len(results)
                    success_items += 1

                    # Record costs for each repeat
                    num_gt_images = len(packet.get("gt_labeled_paths", []))
                    for _ in range(len(results)):
                        cost_tracker.record_call(item_id, num_gt_images)

                    # Check cost thresholds (auto-stop if max exceeded)
                    if not check_cost_threshold(cost_tracker, max_cost_usd=config.scoring.max_cost_usd):
                        console.print("[red]Scoring stopped (cost limit reached).[/red]")
                        break

                # Log elapsed time
                item_elapsed = time.time() - item_start
                console.print(f"[dim]  {item_id}: {item_elapsed:.1f}s ({repeats} repeats)[/dim]")
                console.print(f"[dim]  Running cost: ${cost_tracker.total_cost_usd:.4f}[/dim]")

            except QuotaExhaustedError as e:
                console.print(f"[red]Quota exhausted: {e}[/red]")
                break  # Stop processing if all keys exhausted
            except Exception as e:
                console.print(f"[red]Failed to score {item_id}: {e}[/red]")

            progress.advance(task)

    # Print final key pool statistics
    if key_pool:
        key_pool.print_stats()

        # Save stats to file
        stats_path = base_llm_calls_dir / "key_pool_stats.json"
        key_pool.save_stats(stats_path)

    return total_calls, success_items, skipped_items


def run_scoring(
    config: Config,
    model: str = "gemini-2.5-pro",
    repeats: int = 3,
    temperature: float = None,
    top_p: float = None,
) -> None:
    """Run LLM scoring for all items.

    Args:
        config: Configuration object
        model: Model name to use
        repeats: Number of repeats per item
        temperature: Sampling temperature (overrides config if provided)
        top_p: Top-p sampling (overrides config if provided)
    """

    # Display billing warning (non-interactive)
    if config.scoring.display_billing_warning:
        console.print("\n[bold cyan]Step 1: Billing Information[/bold cyan]")
        display_billing_warning()

    # Load packets
    labels_dir = config.paths.out_dir / "labels"
    if not labels_dir.exists():
        raise FileNotFoundError(f"Labels directory not found: {labels_dir}")

    packets = load_packets(labels_dir)

    if not packets:
        raise ValueError("No scoring packets found. Run 'vfscore package' first.")

    # Use provided parameters or fall back to config
    actual_temperature = temperature if temperature is not None else config.scoring.temperature
    actual_top_p = top_p if top_p is not None else config.scoring.top_p

    # Display cost estimate and check limit (non-interactive)
    if config.scoring.display_cost_estimate:
        console.print("\n[bold cyan]Step 2: Cost Estimation[/bold cyan]")
        estimator = CostEstimator(model)
        estimated_cost, breakdown = estimator.estimate_batch_cost(
            num_items=len(packets),
            repeats_per_item=repeats,
            num_gt_images=3,  # Average GT images per item
        )

        # Check if cost exceeds limit (auto-abort if exceeded)
        if not display_cost_estimate(
            len(packets),
            repeats,
            model,
            estimated_cost,
            breakdown,
            max_cost_usd=config.scoring.max_cost_usd
        ):
            console.print("[red]Scoring aborted (cost limit exceeded).[/red]")
            return

    console.print("\n[bold cyan]Step 3: Starting Scoring[/bold cyan]")
    console.print(f"[bold]Scoring {len(packets)} items with {model} ({repeats} repeats each)...[/bold]")
    console.print(f"[cyan]Temperature: {actual_temperature}, Top-P: {actual_top_p}[/cyan]")

    # Check if async mode enabled
    if config.scoring.use_async:
        console.print("[cyan]Using async mode with intelligent rate limiting[/cyan]")

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
        # Add actual temperature and top_p values
        batch_metadata["temperature"] = actual_temperature
        batch_metadata["top_p"] = actual_top_p
        console.print(f"[cyan]Batch mode enabled: {batch_dir_name}[/cyan]")

    # Normalize model name for directory
    model_dir_name = model.replace("gemini-", "").replace("-", "_")
    if not model_dir_name:
        model_dir_name = "gemini"

    # Initialize cost tracker
    cost_tracker = CostTracker(model, base_llm_calls_dir)
    console.print(f"[cyan]Cost tracking enabled (logs: {base_llm_calls_dir}/cost_tracker.json)[/cyan]")

    # Run scoring (async or sync)
    if config.scoring.use_async:
        # Async mode
        total_calls, success_items, skipped_items = asyncio.run(
            run_scoring_async(
                config=config,
                model=model,
                repeats=repeats,
                actual_temperature=actual_temperature,
                actual_top_p=actual_top_p,
                packets=packets,
                base_llm_calls_dir=base_llm_calls_dir,
                batch_dir_name=batch_dir_name,
                batch_metadata=batch_metadata,
                model_dir_name=model_dir_name,
                cost_tracker=cost_tracker,
            )
        )
    else:
        # Sync mode (backward compatibility)
        total_calls = 0
        success_items = 0
        skipped_items = 0

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Scoring with {model}", total=len(packets))

            for idx, packet in enumerate(packets, 1):
                item_id = packet["item_id"]
                item_start = time.time()

                # Update progress description with current item
                progress.update(task, description=f"Scoring {item_id} ({idx}/{len(packets)})")

                # Build output directory path
                if config.scoring.use_batch_mode:
                    output_dir = base_llm_calls_dir / model_dir_name / item_id / batch_dir_name
                else:
                    # Legacy mode: no batch directory
                    output_dir = base_llm_calls_dir / model_dir_name / item_id

                # Check if item is already scored
                if is_item_already_scored(output_dir, repeats):
                    skipped_items += 1
                    success_items += 1
                    total_calls += repeats
                    console.print(f"[dim]  {item_id}: [yellow]skipped[/yellow] (already scored)[/dim]")
                    progress.advance(task)
                    continue

                output_dir.mkdir(parents=True, exist_ok=True)

                # Save batch metadata once per item
                if config.scoring.use_batch_mode and batch_metadata:
                    batch_info_path = output_dir / "batch_info.json"
                    with open(batch_info_path, "w", encoding="utf-8") as f:
                        json.dump(batch_metadata, f, indent=2, ensure_ascii=False)

                try:
                    results = score_item_with_repeats(
                        packet=packet,
                        model_name=model,
                        temperature=actual_temperature,
                        top_p=actual_top_p,
                        rubric_weights=config.scoring.rubric_weights,
                        repeats=repeats,
                        output_dir=output_dir,
                    )

                    if results:
                        total_calls += len(results)
                        success_items += 1

                        # Record costs for each repeat
                        num_gt_images = len(packet.get("gt_labeled_paths", []))
                        for _ in range(len(results)):
                            cost_tracker.record_call(item_id, num_gt_images)

                        # Check cost thresholds (auto-stop if max exceeded)
                        if not check_cost_threshold(cost_tracker, max_cost_usd=config.scoring.max_cost_usd):
                            console.print("[red]Scoring stopped (cost limit reached).[/red]")
                            break

                    # Log elapsed time for this item
                    item_elapsed = time.time() - item_start
                    console.print(f"[dim]  {item_id}: {item_elapsed:.1f}s ({repeats} repeats)[/dim]")
                    console.print(f"[dim]  Running cost: ${cost_tracker.total_cost_usd:.4f}[/dim]")

                except Exception as e:
                    console.print(f"[red]Failed to score {item_id}: {e}[/red]")

                progress.advance(task)

    # Print summary
    console.print(f"\n[green]Completed {total_calls} API calls for {success_items}/{len(packets)} items[/green]")

    if skipped_items > 0:
        console.print(f"[yellow]Skipped {skipped_items} already-scored items (resume capability)[/yellow]")

    if config.scoring.use_batch_mode:
        console.print(f"[cyan]Results saved in batch: {batch_dir_name}[/cyan]")

    # Save cost logs and print summary
    console.print("\n" + "=" * 80)
    cost_tracker.save_logs()
    cost_tracker.print_summary()
    console.print("=" * 80)

    # Final warning if costs were incurred
    if cost_tracker.total_cost_usd > 0.01:
        console.print()
        console.print("[bold yellow]⚠ COSTS INCURRED ⚠[/bold yellow]")
        console.print(f"[yellow]Total cost: ${cost_tracker.total_cost_usd:.4f} USD (≈€{cost_tracker.total_cost_usd * 0.92:.4f} EUR)[/yellow]")
        console.print("[yellow]Check your Google Cloud billing console for actual charges.[/yellow]")


if __name__ == "__main__":
    from vfscore.config import get_config
    
    config = get_config()
    run_scoring(config, model="gemini-2.5-pro", repeats=3)
