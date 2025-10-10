"""Ground truth photo preprocessing: segmentation, standardization, labeling."""

import json
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from rembg import remove
from rich.console import Console
from rich.progress import track

from vfscore.config import Config

console = Console()


def load_manifest(manifest_path: Path) -> list:
    """Load manifest from JSONL file."""
    records = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


def remove_background(image: Image.Image, model: str = "u2net") -> Image.Image:
    """Remove background using rembg."""
    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    # Remove background
    output = remove(image, session=None)
    
    return output


def get_tight_bbox(alpha: np.ndarray, margin_frac: float = 0.05) -> Tuple[int, int, int, int]:
    """Get tight bounding box from alpha channel with margin."""
    # Find non-zero pixels
    coords = np.column_stack(np.where(alpha > 0))
    
    if len(coords) == 0:
        # Return full image if no foreground detected
        return 0, 0, alpha.shape[1], alpha.shape[0]
    
    # Get bbox
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    
    # Add margin
    h, w = alpha.shape
    margin_x = int((x_max - x_min) * margin_frac)
    margin_y = int((y_max - y_min) * margin_frac)
    
    x_min = max(0, x_min - margin_x)
    y_min = max(0, y_min - margin_y)
    x_max = min(w, x_max + margin_x)
    y_max = min(h, y_max + margin_y)
    
    return x_min, y_min, x_max, y_max


def crop_and_pad(image: Image.Image, canvas_size: int, bg_color: Tuple[int, int, int]) -> Image.Image:
    """Crop to content and pad to square canvas with black background."""
    # Get alpha channel
    if image.mode == "RGBA":
        alpha = np.array(image.split()[3])
    else:
        # If no alpha, assume full image is foreground
        alpha = np.ones((image.height, image.width), dtype=np.uint8) * 255
    
    # Get tight bbox
    x_min, y_min, x_max, y_max = get_tight_bbox(alpha)
    
    # Crop
    cropped = image.crop((x_min, y_min, x_max, y_max))
    
    # Create square canvas
    canvas = Image.new("RGB", (canvas_size, canvas_size), bg_color)
    
    # Calculate paste position (center)
    paste_w, paste_h = cropped.size
    
    # Scale down if too large
    if paste_w > canvas_size or paste_h > canvas_size:
        scale = min(canvas_size / paste_w, canvas_size / paste_h)
        new_w = int(paste_w * scale)
        new_h = int(paste_h * scale)
        cropped = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
        paste_w, paste_h = new_w, new_h
    
    paste_x = (canvas_size - paste_w) // 2
    paste_y = (canvas_size - paste_h) // 2
    
    # Paste with alpha if available
    if cropped.mode == "RGBA":
        canvas.paste(cropped, (paste_x, paste_y), cropped)
    else:
        canvas.paste(cropped, (paste_x, paste_y))
    
    return canvas


def add_label(image: Image.Image, label: str, bar_frac: float = 0.06) -> Image.Image:
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


def preprocess_gt_image(
    input_path: Path,
    output_path: Path,
    label: str,
    config: Config,
) -> None:
    """Preprocess a single GT image."""
    # Load image
    image = Image.open(input_path)
    
    # Convert to sRGB
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    # Remove background
    image_no_bg = remove_background(image, config.preprocess.segmentation_model)
    
    # Crop and pad
    standardized = crop_and_pad(
        image_no_bg,
        config.preprocess.canvas_px,
        tuple(config.preprocess.bg_rgb)
    )
    
    # Add label (but not yet - we'll do this in packetize step for consistency)
    # For now just save the standardized image
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    standardized.save(output_path, "PNG")


def run_preprocess_gt(config: Config) -> None:
    """Run ground truth preprocessing for all items."""
    # Load manifest
    manifest_path = config.paths.out_dir / "manifest.jsonl"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}. Run 'vfscore ingest' first.")
    
    manifest = load_manifest(manifest_path)
    
    console.print(f"\n[bold]Processing {len(manifest)} items...[/bold]")
    
    total_images = sum(record["n_refs"] for record in manifest)
    
    processed = 0
    for record in track(manifest, description="Preprocessing GT images"):
        item_id = record["item_id"]
        ref_paths = [Path(p) for p in record["ref_paths"]]
        
        for idx, ref_path in enumerate(ref_paths, start=1):
            output_path = (
                config.paths.out_dir / "preprocess" / "refs" / item_id / f"gt_{idx}.png"
            )
            
            try:
                preprocess_gt_image(
                    ref_path,
                    output_path,
                    f"GT #{idx}",
                    config,
                )
                processed += 1
            except Exception as e:
                console.print(f"[red]Error processing {ref_path}: {e}[/red]")
    
    console.print(f"[green]Processed {processed}/{total_images} images[/green]")


if __name__ == "__main__":
    from vfscore.config import get_config
    
    config = get_config()
    run_preprocess_gt(config)
