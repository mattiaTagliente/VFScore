"""Score aggregation: compute medians and confidence metrics."""

import csv
import json
import math
from pathlib import Path
from typing import Dict, List

import numpy as np
from rich.console import Console
from rich.progress import track

from vfscore.config import Config

console = Console()


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


def aggregate_item(item_id: str, llm_calls_dir: Path, models: List[str]) -> Dict:
    """Aggregate results for a single item across all models."""
    
    model_results = {}
    all_scores = []
    
    for model in models:
        item_dir = llm_calls_dir / model / item_id
        
        if not item_dir.exists():
            console.print(f"[yellow]Warning: No results for {item_id} with {model}[/yellow]")
            continue
        
        repeats = load_repeats(item_dir, model)
        
        if not repeats:
            console.print(f"[yellow]Warning: No repeats found for {item_id} with {model}[/yellow]")
            continue
        
        agg = aggregate_model_results(repeats)
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
    
    return {
        "item_id": item_id,
        "scores": model_results,
        "final_score": round(final_score, 2),
        "confidence": round(confidence, 2),
        "mad": round(mad, 2),
        "flags": [],
    }


def run_aggregation(config: Config) -> None:
    """Aggregate all scores and create results files."""
    
    llm_calls_dir = config.paths.out_dir / "llm_calls"
    
    if not llm_calls_dir.exists():
        raise FileNotFoundError(f"LLM calls directory not found: {llm_calls_dir}")
    
    # Get available models
    models = [d.name for d in llm_calls_dir.iterdir() if d.is_dir()]
    
    if not models:
        raise ValueError("No model results found. Run 'vfscore score' first.")
    
    console.print(f"\n[bold]Aggregating results for models: {', '.join(models)}[/bold]")
    
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
        result = aggregate_item(item_id, llm_calls_dir, models)
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
            result["l1"] = manifest_record["l1"]
            result["l2"] = manifest_record["l2"]
            result["l3"] = manifest_record["l3"]
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
        header = ["item_id", "l1", "l2", "l3", "n_gt", "final_score", "confidence", "mad"]
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
