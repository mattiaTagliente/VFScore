"""
Reorganize datasets to match VFScore expected structure.

VFScore expects:
  datasets/refs/<item_id>/*.jpg
  datasets/gens/<item_id>/*.glb

This script moves loose files in the root of refs/ and gens/ into their
respective item_id subdirectories.
"""

import re
from pathlib import Path
import shutil

def extract_item_id(filename: str) -> str:
    """Extract item_id from filename.

    Examples:
        188368__hunyuan3d... -> 188368
        335888_curved-backrest... -> 335888
        558736_7-1-emko... -> 558736
    """
    # Try to match numeric ID at start (most common pattern)
    match = re.match(r'^(\d+)', filename)
    if match:
        return match.group(1)

    # Fallback: use first part before _ or __
    if '__' in filename:
        return filename.split('__')[0]
    elif '_' in filename:
        return filename.split('_')[0]

    # Last resort: use filename without extension
    return Path(filename).stem


def reorganize_directory(directory: Path, file_extensions: list) -> None:
    """Reorganize files in directory into item_id subdirectories.

    Args:
        directory: Path to refs or gens directory
        file_extensions: List of file extensions to process (e.g., ['.jpg', '.png'])
    """
    if not directory.exists():
        print(f"[WARNING] Directory not found: {directory}")
        return

    print(f"\n{'='*80}")
    print(f"Reorganizing: {directory}")
    print(f"{'='*80}")

    # Find all loose files in root of directory
    loose_files = []
    for ext in file_extensions:
        loose_files.extend(directory.glob(f"*{ext}"))

    if not loose_files:
        print("[OK] No loose files found - directory already organized")
        return

    print(f"Found {len(loose_files)} loose files to reorganize\n")

    # Group files by item_id
    files_by_item = {}
    for file_path in loose_files:
        item_id = extract_item_id(file_path.name)
        if item_id not in files_by_item:
            files_by_item[item_id] = []
        files_by_item[item_id].append(file_path)

    # Move files into subdirectories
    for item_id, files in sorted(files_by_item.items()):
        item_dir = directory / item_id

        # Create subdirectory if it doesn't exist
        if not item_dir.exists():
            print(f"Creating directory: {item_id}/")
            item_dir.mkdir(parents=True, exist_ok=True)

        # Move files
        for file_path in files:
            dest_path = item_dir / file_path.name

            if dest_path.exists():
                print(f"  [SKIP] {file_path.name} (already exists in {item_id}/)")
            else:
                print(f"  [MOVE] {file_path.name} -> {item_id}/")
                shutil.move(str(file_path), str(dest_path))

    print(f"\n[OK] Reorganization complete for {directory.name}")


def verify_structure(refs_dir: Path, gens_dir: Path) -> None:
    """Verify the reorganized structure is correct."""
    print(f"\n{'='*80}")
    print("VERIFICATION")
    print(f"{'='*80}")

    # Check refs
    refs_items = [d for d in refs_dir.iterdir() if d.is_dir()]
    print(f"\nRefs directory: {len(refs_items)} item folders")
    for item_dir in sorted(refs_items):
        photos = list(item_dir.glob("*.jpg")) + list(item_dir.glob("*.jpeg")) + list(item_dir.glob("*.png"))
        print(f"  {item_dir.name}: {len(photos)} photo(s)")

    # Check gens
    gens_items = [d for d in gens_dir.iterdir() if d.is_dir()]
    print(f"\nGens directory: {len(gens_items)} item folders")
    for item_dir in sorted(gens_items):
        glbs = list(item_dir.glob("*.glb"))
        print(f"  {item_dir.name}: {len(glbs)} model(s)")

    # Check for items with both refs and gens
    refs_ids = {d.name for d in refs_items}
    gens_ids = {d.name for d in gens_items}

    valid_items = refs_ids & gens_ids
    refs_only = refs_ids - gens_ids
    gens_only = gens_ids - refs_ids

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"[OK] Items with both refs and gens: {len(valid_items)}")
    if refs_only:
        print(f"[WARN] Items with refs only: {len(refs_only)} - {sorted(refs_only)}")
    if gens_only:
        print(f"[WARN] Items with gens only: {len(gens_only)} - {sorted(gens_only)}")

    if valid_items:
        print(f"\n[OK] Ready to run: vfscore ingest")
        print(f"  This will process {len(valid_items)} items")


def main():
    """Main reorganization script."""
    import sys

    project_root = Path(__file__).parent
    refs_dir = project_root / "datasets" / "refs"
    gens_dir = project_root / "datasets" / "gens"

    print("="*80)
    print("VFScore Dataset Reorganization")
    print("="*80)
    print("\nThis script will reorganize your datasets to match VFScore's expected structure:")
    print("  datasets/refs/<item_id>/*.jpg")
    print("  datasets/gens/<item_id>/*.glb")
    print("\nAny loose files in the root of refs/ or gens/ will be moved into")
    print("subdirectories based on their item_id (extracted from filename).")

    # Check for --yes flag
    skip_prompt = '--yes' in sys.argv or '-y' in sys.argv

    if not skip_prompt:
        response = input("\nProceed? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("\n[CANCELLED] Reorganization cancelled by user.")
            return
    else:
        print("\n[INFO] Running with --yes flag, skipping confirmation")

    # Reorganize refs directory
    reorganize_directory(refs_dir, ['.jpg', '.jpeg', '.png'])

    # Reorganize gens directory
    reorganize_directory(gens_dir, ['.glb'])

    # Verify final structure
    verify_structure(refs_dir, gens_dir)

    print(f"\n{'='*80}")
    print("REORGANIZATION COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
