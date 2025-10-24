"""Score aggregation: compute medians and confidence metrics."""

import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from rich.console import Console
from rich.progress import track

from vfscore.config import Config

console = Console()


def discover_batch_directories(item_dir: Path) -> List[Path]:
    """Discover all batch directories within an item directory.

    Supports both new batch structure and legacy (no batch) structure.

    Args:
        item_dir: Path to item directory (e.g., outputs/llm_calls/gemini/558736/)

    Returns:
        List of batch directory paths (or [item_dir] for legacy structure)
    """
    if not item_dir.exists():
        return []

    # Look for batch directories (batch_*)
    batch_dirs = sorted([d for d in item_dir.iterdir() if d.is_dir() and d.name.startswith("batch_")])

    if batch_dirs:
        return batch_dirs

    # Legacy structure: item_dir itself contains rep_*.json files
    if list(item_dir.glob("rep_*.json")):
        return [item_dir]

    return []


def filter_batch_directories(
    batch_dirs: List[Path],
    latest_only: bool = False,
    batch_pattern: Optional[str] = None,
    after_date: Optional[str] = None,
) -> List[Path]:
    """Filter batch directories based on criteria.

    Args:
        batch_dirs: List of batch directory paths
        latest_only: If True, return only the latest batch
        batch_pattern: Filter batches containing this string in their name
        after_date: Filter batches after this date (YYYY-MM-DD format)

    Returns:
        Filtered list of batch directories
    """
    filtered = batch_dirs

    # Apply pattern filter
    if batch_pattern:
        filtered = [d for d in filtered if batch_pattern in d.name]

    # Apply date filter
    if after_date:
        try:
            cutoff_date = datetime.strptime(after_date, "%Y-%m-%d")
            filtered = []
            for d in batch_dirs:
                # Extract timestamp from batch directory name
                # Format: batch_YYYYMMDD_HHMMSS_user_<username>
                if d.name.startswith("batch_"):
                    try:
                        date_str = d.name.split("_")[1]  # YYYYMMDD
                        batch_date = datetime.strptime(date_str, "%Y%m%d")
                        if batch_date >= cutoff_date:
                            filtered.append(d)
                    except (IndexError, ValueError):
                        # Can't parse date, skip
                        continue
                else:
                    # Legacy batch, include by default
                    filtered.append(d)
        except ValueError:
            console.print(f"[yellow]Warning: Invalid date format '{after_date}', ignoring date filter[/yellow]")
            filtered = batch_dirs

    # Apply latest_only filter
    if latest_only and filtered:
        # Sort by directory name (timestamp is embedded)
        filtered = [sorted(filtered, reverse=True)[0]]

    return filtered


def load_repeats(item_dir: Path, model: str) -> List[Dict]:
    """Load all repeat results for an item and model."""
    results = []
    
    for rep_file in sorted(item_dir.glob("rep_*.json")):
        with open(rep_file, "r", encoding="utf-8") as f:
            results.append(json.load(f))
    
    return results


def compute_median(values: List[float]) -> float:
    """Compute median of a list of values."""
    if not values:
        return 0.0
    return float(np.median(values))


def compute_mad(values: List[float]) -> float:
    """Compute Median Absolute Deviation."""
    if len(values) < 2:
        return 0.0
    
    median = np.median(values)
    mad = np.median([abs(v - median) for v in values])
    return float(mad)


def compute_confidence(mad: float) -> float:
    """Compute confidence from MAD using exponential decay.
    
    conf = max(0, min(1, exp(-MAD/5)))
    """
    return max(0.0, min(1.0, math.exp(-mad / 5.0)))


def aggregate_model_results(results: List[Dict]) -> Dict:
    """Aggregate results from multiple repeats for a single model."""
    if not results:
        return {
            "repeats": [],
            "median": 0,
            "subscores_median": {},
        }
    
    # Extract scores
    scores = [r["score"] for r in results]
    
    # Extract subscores
    subscore_keys = list(results[0]["subscores"].keys())
    subscores_by_dimension = {
        key: [r["subscores"][key] for r in results]
        for key in subscore_keys
    }
    
    # Compute medians
    median_score = compute_median(scores)
    subscores_median = {
        key: compute_median(values)
        for key, values in subscores_by_dimension.items()
    }
    
    return {
        "repeats": scores,
        "median": int(round(median_score)),
        "subscores_median": {k: int(round(v)) for k, v in subscores_median.items()},
    }


def aggregate_item(
    item_id: str,
    llm_calls_dir: Path,
    models: List[str],
    latest_only: bool = False,
    batch_pattern: Optional[str] = None,
    after_date: Optional[str] = None,
) -> Dict:
    """Aggregate results for a single item across all models and batches.

    Args:
        item_id: Item identifier
        llm_calls_dir: Base directory containing LLM call results
        models: List of model names
        latest_only: If True, use only the latest batch per item
        batch_pattern: Filter batches containing this string
        after_date: Filter batches after this date (YYYY-MM-DD)

    Returns:
        Aggregated results dictionary
    """

    model_results = {}
    all_scores = []
    batch_info_list = []

    for model in models:
        item_dir = llm_calls_dir / model / item_id

        if not item_dir.exists():
            console.print(f"[yellow]Warning: No results for {item_id} with {model}[/yellow]")
            continue

        # Discover all batch directories for this item
        batch_dirs = discover_batch_directories(item_dir)

        # Apply filters
        batch_dirs = filter_batch_directories(
            batch_dirs,
            latest_only=latest_only,
            batch_pattern=batch_pattern,
            after_date=after_date,
        )

        if not batch_dirs:
            console.print(f"[yellow]Warning: No batches found for {item_id} with {model}[/yellow]")
            continue

        # Collect repeats from all batches
        all_repeats = []
        for batch_dir in batch_dirs:
            repeats = load_repeats(batch_dir, model)
            all_repeats.extend(repeats)

            # Load batch metadata if available
            batch_info_path = batch_dir / "batch_info.json"
            if batch_info_path.exists():
                try:
                    with open(batch_info_path, "r", encoding="utf-8") as f:
                        batch_info = json.load(f)
                        batch_info["batch_dir"] = batch_dir.name
                        batch_info_list.append(batch_info)
                except Exception:
                    pass

        if not all_repeats:
            console.print(f"[yellow]Warning: No repeats found for {item_id} with {model}[/yellow]")
            continue

        # Aggregate across all batches
        agg = aggregate_model_results(all_repeats)
        model_results[model] = agg

        # Collect all scores for confidence
        all_scores.extend(agg["repeats"])

    # Compute final score (mean of model medians)
    if model_results:
        model_medians = [agg["median"] for agg in model_results.values()]
        final_score = np.mean(model_medians)
    else:
        final_score = 0.0

    # Compute confidence from all scores
    mad = compute_mad(all_scores)
    confidence = compute_confidence(mad)

    result = {
        "item_id": item_id,
        "scores": model_results,
        "final_score": round(final_score, 2),
        "confidence": round(confidence, 2),
        "mad": round(mad, 2),
        "flags": [],
        "n_batches": len(set([b["batch_dir"] for b in batch_info_list if "batch_dir" in b])) if batch_info_list else 0,
        "n_total_repeats": len(all_scores),
    }

    # Add batch info for provenance
    if batch_info_list:
        result["batches"] = batch_info_list

    return result


def run_aggregation(
    config: Config,
    latest_only: bool = False,
    batch_pattern: Optional[str] = None,
    after_date: Optional[str] = None,
) -> None:
    """Aggregate all scores and create results files.

    Args:
        config: Configuration object
        latest_only: If True, use only the latest batch per item (default: False, use all batches)
        batch_pattern: Filter batches containing this string in their name
        after_date: Filter batches after this date (YYYY-MM-DD format)
    """

    # Determine LLM calls directory
    if config.scoring.results_dir:
        llm_calls_dir = Path(config.scoring.results_dir)
        console.print(f"[cyan]Using shared results directory: {llm_calls_dir}[/cyan]")
    else:
        llm_calls_dir = config.paths.out_dir / "llm_calls"

    if not llm_calls_dir.exists():
        raise FileNotFoundError(f"LLM calls directory not found: {llm_calls_dir}")

    # Get available models
    models = [d.name for d in llm_calls_dir.iterdir() if d.is_dir()]

    if not models:
        raise ValueError("No model results found. Run 'vfscore score' first.")

    # Print aggregation mode
    if latest_only:
        console.print(f"\n[bold]Aggregating results (LATEST BATCH ONLY) for models: {', '.join(models)}[/bold]")
    else:
        console.print(f"\n[bold]Aggregating results (ALL BATCHES) for models: {', '.join(models)}[/bold]")

    if batch_pattern:
        console.print(f"[cyan]Filtering batches with pattern: '{batch_pattern}'[/cyan]")
    if after_date:
        console.print(f"[cyan]Filtering batches after: {after_date}[/cyan]")

    # Get all item IDs
    item_ids = set()
    for model in models:
        model_dir = llm_calls_dir / model
        for item_dir in model_dir.iterdir():
            if item_dir.is_dir():
                item_ids.add(item_dir.name)

    item_ids = sorted(item_ids)

    console.print(f"Found {len(item_ids)} items to aggregate")

    # Aggregate each item
    aggregated_results = []

    for item_id in track(item_ids, description="Aggregating"):
        result = aggregate_item(
            item_id,
            llm_calls_dir,
            models,
            latest_only=latest_only,
            batch_pattern=batch_pattern,
            after_date=after_date,
        )
        aggregated_results.append(result)
    
    # Load manifest for category info
    manifest_path = config.paths.out_dir / "manifest.jsonl"
    manifest_map = {}
    
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                manifest_map[record["item_id"]] = record
    
    # Enrich results with manifest data
    for result in aggregated_results:
        item_id = result["item_id"]
        if item_id in manifest_map:
            manifest_record = manifest_map[item_id]
            result["l1"] = manifest_record["category_l1"]
            result["l2"] = manifest_record["category_l2"]
            result["l3"] = manifest_record["category_l3"]
            result["n_gt"] = manifest_record["n_refs"]
    
    # Create output directory
    results_dir = config.paths.out_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSONL
    jsonl_path = results_dir / "per_item.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for result in aggregated_results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    console.print(f"[green]Saved JSONL: {jsonl_path}[/green]")
    
    # Save CSV
    csv_path = results_dir / "per_item.csv"
    
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header
        header = ["item_id", "l1", "l2", "l3", "n_gt", "final_score", "confidence", "mad", "n_batches", "n_total_repeats"]
        for model in models:
            header.append(f"{model}_median")
        header.append("flags")

        writer.writerow(header)

        # Rows
        for result in aggregated_results:
            row = [
                result["item_id"],
                result.get("l1", ""),
                result.get("l2", ""),
                result.get("l3", ""),
                result.get("n_gt", ""),
                result["final_score"],
                result["confidence"],
                result["mad"],
                result.get("n_batches", 0),
                result.get("n_total_repeats", 0),
            ]

            for model in models:
                if model in result["scores"]:
                    row.append(result["scores"][model]["median"])
                else:
                    row.append("")

            row.append(",".join(result["flags"]))

            writer.writerow(row)
    
    console.print(f"[green]Saved CSV: {csv_path}[/green]")
    
    # Print summary statistics
    scores = [r["final_score"] for r in aggregated_results]
    confidences = [r["confidence"] for r in aggregated_results]
    
    console.print("\n[bold]Summary Statistics:[/bold]")
    console.print(f"  Mean score: {np.mean(scores):.2f}")
    console.print(f"  Median score: {np.median(scores):.2f}")
    console.print(f"  Std dev: {np.std(scores):.2f}")
    console.print(f"  Mean confidence: {np.mean(confidences):.2f}")


if __name__ == "__main__":
    from vfscore.config import get_config
    
    config = get_config()
    run_aggregation(config)
