"""Data ingestion: scan datasets and create manifest."""

import csv
import json
from pathlib import Path
from typing import Dict, List

from rich.console import Console
from rich.progress import track

from vfscore.config import Config

console = Console()


def scan_references(refs_dir: Path) -> Dict[str, List[Path]]:
    """Scan reference photos directory and return mapping of item_id -> photo paths."""
    refs_map = {}
    
    if not refs_dir.exists():
        raise FileNotFoundError(f"References directory not found: {refs_dir}")
    
    for item_dir in refs_dir.iterdir():
        if not item_dir.is_dir():
            continue
        
        item_id = item_dir.name
        photo_paths = []
        
        for photo_path in item_dir.glob("*"):
            if photo_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                photo_paths.append(photo_path)
        
        if photo_paths:
            refs_map[item_id] = sorted(photo_paths)
    
    return refs_map


def scan_generated(gens_dir: Path) -> Dict[str, Path]:
    """Scan generated objects directory and return mapping of item_id -> glb path."""
    gens_map = {}
    
    if not gens_dir.exists():
        raise FileNotFoundError(f"Generated objects directory not found: {gens_dir}")
    
    for item_dir in gens_dir.iterdir():
        if not item_dir.is_dir():
            continue
        
        item_id = item_dir.name
        glb_files = list(item_dir.glob("*.glb"))
        
        if len(glb_files) == 0:
            console.print(f"[yellow]Warning:[/yellow] No .glb file found for item {item_id}")
            continue
        
        if len(glb_files) > 1:
            console.print(f"[yellow]Warning:[/yellow] Multiple .glb files for item {item_id}, using first one")
        
        gens_map[item_id] = glb_files[0]
    
    return gens_map


def load_categories(categories_path: Path) -> Dict[str, Dict[str, str]]:
    """Load category metadata from CSV."""
    categories_map = {}
    
    if not categories_path.exists():
        raise FileNotFoundError(f"Categories file not found: {categories_path}")
    
    with open(categories_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_id = row["item_id"]
            categories_map[item_id] = {
                "l1": row["l1"],
                "l2": row["l2"],
                "l3": row["l3"],
            }
    
    return categories_map


def create_manifest(
    refs_map: Dict[str, List[Path]],
    gens_map: Dict[str, Path],
    categories_map: Dict[str, Dict[str, str]],
    output_path: Path,
) -> None:
    """Create manifest JSONL file with all item metadata."""
    # Find items that have both references and generated objects
    valid_items = set(refs_map.keys()) & set(gens_map.keys())
    
    if not valid_items:
        raise ValueError("No valid items found (items must have both refs and gens)")
    
    # Check for items without categories
    missing_categories = valid_items - set(categories_map.keys())
    if missing_categories:
        console.print(f"[yellow]Warning:[/yellow] Items without categories: {missing_categories}")
    
    manifest_records = []
    
    for item_id in sorted(valid_items):
        # Get categories or use defaults
        categories = categories_map.get(item_id, {"l1": "unknown", "l2": "unknown", "l3": "unknown"})
        
        record = {
            "item_id": item_id,
            "ref_paths": [str(p) for p in refs_map[item_id]],
            "glb_path": str(gens_map[item_id]),
            "n_refs": len(refs_map[item_id]),
            "l1": categories["l1"],
            "l2": categories["l2"],
            "l3": categories["l3"],
        }
        
        manifest_records.append(record)
    
    # Write manifest
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for record in manifest_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    console.print(f"[green]Manifest created with {len(manifest_records)} items[/green]")
    
    # Print summary
    console.print("\n[bold]Summary by category (l3):[/bold]")
    l3_counts = {}
    for record in manifest_records:
        l3 = record["l3"]
        l3_counts[l3] = l3_counts.get(l3, 0) + 1
    
    for l3, count in sorted(l3_counts.items()):
        console.print(f"  {l3}: {count} items")


def run_ingest(config: Config) -> Path:
    """Run the ingestion process."""
    console.print("\n[bold]Scanning datasets...[/bold]")
    
    # Scan directories
    refs_map = scan_references(config.paths.refs_dir)
    console.print(f"Found {len(refs_map)} items with reference photos")
    
    gens_map = scan_generated(config.paths.gens_dir)
    console.print(f"Found {len(gens_map)} items with generated objects")
    
    categories_map = load_categories(config.paths.categories)
    console.print(f"Loaded {len(categories_map)} category entries")
    
    # Create manifest
    manifest_path = config.paths.out_dir / "manifest.jsonl"
    create_manifest(refs_map, gens_map, categories_map, manifest_path)
    
    return manifest_path


if __name__ == "__main__":
    from vfscore.config import get_config
    
    config = get_config()
    run_ingest(config)
