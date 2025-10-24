"""Package scoring units: add labels and create scoring packets."""

import json
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.progress import track

from vfscore.config import Config

console = Console()


def add_label_bar(image: Image.Image, label: str, bar_frac: float = 0.06) -> Image.Image:
    """Add label bar at the top of the image."""
    w, h = image.size
    bar_height = int(h * bar_frac)
    
    # Create new image with space for label
    labeled = Image.new("RGB", (w, h + bar_height), (0, 0, 0))
    labeled.paste(image, (0, bar_height))
    
    # Draw label
    draw = ImageDraw.Draw(labeled)
    
    # Try to use a nice font, fall back to default if not available
    try:
        font_size = int(bar_height * 0.6)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Get text bbox
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Center text
    text_x = (w - text_w) // 2
    text_y = (bar_height - text_h) // 2
    
    draw.text((text_x, text_y), label, fill=(255, 255, 255), font=font)
    
    return labeled


def load_manifest(manifest_path: Path) -> list:
    """Load manifest from JSONL file."""
    records = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


def create_labeled_images(
    item_id: str,
    n_refs: int,
    refs_dir: Path,
    cand_dir: Path,
    output_dir: Path,
    config: Config,
) -> dict:
    """Create labeled images for an item and return packet info."""
    
    # Process GT images
    gt_labeled_paths = []
    gt_labels = []
    
    for idx in range(1, n_refs + 1):
        gt_path = refs_dir / item_id / f"gt_{idx}.png"
        
        if not gt_path.exists():
            console.print(f"[yellow]Warning: GT image not found: {gt_path}[/yellow]")
            continue
        
        # Load and add label
        image = Image.open(gt_path)
        label = f"GT #{idx}"
        labeled = add_label_bar(image, label, config.preprocess.label_bar_frac)
        
        # Save labeled image
        labeled_path = output_dir / f"gt_{idx}_labeled.png"
        labeled.save(labeled_path, "PNG")
        
        gt_labeled_paths.append(str(labeled_path))
        gt_labels.append(label)
    
    # Process candidate image
    cand_path = cand_dir / item_id / "candidate.png"
    
    if not cand_path.exists():
        raise FileNotFoundError(f"Candidate image not found: {cand_path}")
    
    image = Image.open(cand_path)
    labeled = add_label_bar(image, "CANDIDATE", config.preprocess.label_bar_frac)
    
    cand_labeled_path = output_dir / "candidate_labeled.png"
    labeled.save(cand_labeled_path, "PNG")
    
    return {
        "gt_labeled_paths": gt_labeled_paths,
        "gt_labels": gt_labels,
        "cand_labeled_path": str(cand_labeled_path),
        "n_gt": len(gt_labeled_paths),
    }


def run_packetize(config: Config) -> None:
    """Create labeled images and scoring packets for all items."""
    
    # Load manifest
    manifest_path = config.paths.out_dir / "manifest.jsonl"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    manifest = load_manifest(manifest_path)
    
    # Paths
    refs_dir = config.paths.out_dir / "preprocess" / "refs"
    cand_dir = config.paths.out_dir / "preprocess" / "cand"
    labels_dir = config.paths.out_dir / "labels"
    
    console.print(f"\n[bold]Creating labeled images and packets for {len(manifest)} items...[/bold]")
    
    success_count = 0
    
    for record in track(manifest, description="Packetizing"):
        item_id = record["item_id"]
        output_dir = labels_dir / item_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Create labeled images
            packet_info = create_labeled_images(
                item_id,
                record["n_refs"],
                refs_dir,
                cand_dir,
                output_dir,
                config
            )
            
            # Create packet JSON
            packet = {
                "item_id": item_id,
                "l1": record["category_l1"],
                "l2": record["category_l2"],
                "l3": record["category_l3"],
                "gt_count": packet_info["n_gt"],
                "gt_labeled_paths": packet_info["gt_labeled_paths"],
                "gt_labels": packet_info["gt_labels"],
                "cand_labeled_path": packet_info["cand_labeled_path"],
                "candidate_label": "CANDIDATE",
            }
            
            # Save packet
            packet_path = output_dir / "packet.json"
            with open(packet_path, "w", encoding="utf-8") as f:
                json.dump(packet, f, indent=2, ensure_ascii=False)
            
            success_count += 1
            
        except Exception as e:
            console.print(f"[red]Failed to packetize {item_id}: {e}[/red]")
    
    console.print(f"[green]Successfully created {success_count}/{len(manifest)} packets[/green]")


if __name__ == "__main__":
    from vfscore.config import get_config
    
    config = get_config()
    run_packetize(config)
