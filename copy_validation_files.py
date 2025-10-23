"""Copy selected validation study files to VFScore project directories."""

import csv
import shutil
from pathlib import Path

# Paths
PROJECT_ROOT = Path("C:/Users/matti/OneDrive - Politecnico di Bari (1)/Dev/VFScore")
MODELS_SOURCE = Path("C:/Users/matti/OneDrive - Politecnico di Bari (1)/PhD/Scuole/BinP4Venture/3d-testing/test_models")
DATASET_SOURCE = Path("C:/Users/matti/Politecnico di Bari(1)/B4V - Archiproducts - General/Testing/dataset")

GENS_DEST = PROJECT_ROOT / "datasets" / "gens"
REFS_DEST = PROJECT_ROOT / "datasets" / "refs"

# Create destination directories
GENS_DEST.mkdir(parents=True, exist_ok=True)
REFS_DEST.mkdir(parents=True, exist_ok=True)

# Read selected objects
selected_objects = []
with open(PROJECT_ROOT / "selected_objects_for_study.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        selected_objects.append(row)

print(f"Found {len(selected_objects)} selected objects")
print("=" * 80)

# Track unique product IDs for ground truth images
unique_product_ids = set()

# Copy 3D models
print("\nCopying 3D models to datasets/gens/...")
print("-" * 80)
for obj in selected_objects:
    filename = obj["3D Object filename"]
    product_id = obj["product_id"]
    unique_product_ids.add(product_id)

    # Source file (in test_models directory)
    source_file = MODELS_SOURCE / filename
    dest_file = GENS_DEST / filename

    if source_file.exists():
        shutil.copy2(source_file, dest_file)
        print(f"[OK] Copied: {filename}")
    else:
        print(f"[ERROR] NOT FOUND: {source_file}")

# Copy ground truth images
print("\n\nCopying ground truth images to datasets/refs/...")
print("-" * 80)
for product_id in sorted(unique_product_ids):
    # Look for directories matching this product_id
    # They could be: <product_id>, <product_id> - <variant>
    found_images = []

    # Search for product directory in DATASET_SOURCE
    matching_dirs = [d for d in DATASET_SOURCE.iterdir() if d.is_dir() and d.name.startswith(product_id)]

    if matching_dirs:
        print(f"\nProduct {product_id}:")
        for product_dir in matching_dirs:
            print(f"  Searching in: {product_dir.name}")
            # Get all image files from this directory and subdirectories (especially 'images' subdir)
            for ext in ["*.jpg", "*.png", "*.jpeg", "*.JPG", "*.PNG", "*.JPEG"]:
                # Search in directory and all subdirectories
                for img_file in product_dir.rglob(ext):
                    # Skip if it's in a 'gt' directory (we want ground truth photos, not 3D generated ones)
                    if 'gt' in img_file.parts:
                        continue
                    # Copy with modified name to include product_id prefix if not already there
                    dest_name = f"{product_id}_{img_file.name}" if not img_file.name.startswith(product_id) else img_file.name
                    dest_file = REFS_DEST / dest_name
                    shutil.copy2(img_file, dest_file)
                    print(f"    [OK] Copied: {img_file.name} -> {dest_name}")
                    found_images.append(img_file)

        if not found_images:
            print(f"  [WARNING] No images found in directories for product {product_id}")
    else:
        print(f"\n[ERROR] Product {product_id}: No directory found in {DATASET_SOURCE}")

print("\n" + "=" * 80)
print("File copying complete!")
print(f"\n3D models destination: {GENS_DEST}")
print(f"Ground truth images destination: {REFS_DEST}")
print(f"\nUnique products: {len(unique_product_ids)}")
print(f"Total 3D models: {len(selected_objects)}")
