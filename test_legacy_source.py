"""
Test script for LegacySource data abstraction layer.

This script validates that LegacySource can correctly read and parse
the validation study data from database.csv and the dataset folder.
"""

from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vfscore.data_sources import LegacySource


def main():
    print("="*80)
    print("Testing LegacySource Data Abstraction Layer")
    print("="*80)

    # Setup paths
    vfscore_root = Path(__file__).parent
    database_csv = vfscore_root / "database.csv"
    dataset_folder = Path(r"C:\Users\Shadow\OneDrive - Politecnico di Bari (1)\PhD\Scuole\BinP4Venture\3d-testing\dataset")
    selected_objects_csv = vfscore_root / "selected_objects_optimized.csv"

    print(f"\nConfiguration:")
    print(f"  VFScore root: {vfscore_root}")
    print(f"  Database CSV: {database_csv}")
    print(f"  Dataset folder: {dataset_folder}")
    print(f"  Selected objects CSV: {selected_objects_csv}")

    # Validate paths exist
    print(f"\nValidating paths...")
    if not database_csv.exists():
        print(f"  [ERROR] database.csv not found!")
        return 1
    else:
        print(f"  [OK] database.csv exists")

    if not dataset_folder.exists():
        print(f"  [ERROR] Dataset folder not found!")
        return 1
    else:
        print(f"  [OK] Dataset folder exists")

    if not selected_objects_csv.exists():
        print(f"  [WARNING] selected_objects_optimized.csv not found (optional)")
        selected_objects_csv = None
    else:
        print(f"  [OK] selected_objects_optimized.csv exists")

    # Create LegacySource
    print(f"\nInitializing LegacySource...")
    try:
        source = LegacySource(
            database_csv=database_csv,
            dataset_folder=dataset_folder,
            selected_objects_csv=selected_objects_csv,
            vfscore_root=vfscore_root,
        )
        print(f"  [OK] LegacySource initialized successfully")
    except Exception as e:
        print(f"  [ERROR] Failed to initialize LegacySource: {e}")
        return 1

    # Print source info
    print(f"\nSource Info:")
    source_info = source.get_source_info()
    for key, value in source_info.items():
        print(f"  {key}: {value}")

    # Load items
    print(f"\n{'='*80}")
    print("Loading Items")
    print(f"{'='*80}\n")

    try:
        items = list(source.load_items())
        print(f"\n{'='*80}")
        print(f"RESULTS")
        print(f"{'='*80}")
        print(f"Successfully loaded {len(items)} ItemRecords\n")

        if items:
            print("Sample ItemRecords (first 3):")
            for i, item in enumerate(items[:3], 1):
                print(f"\n{i}. Item: {item.item_id}")
                print(f"   Product ID: {item.product_id}")
                print(f"   Variant: '{item.variant}'")
                print(f"   Algorithm: {item.algorithm}")
                print(f"   Job ID: {item.job_id}")
                print(f"   Ref images: {len(item.ref_image_paths)} files")
                for img_path in item.ref_image_paths:
                    print(f"     - {img_path.name}")
                print(f"   GLB path: {item.glb_path}")
                if item.glb_path:
                    exists = item.glb_path.exists()
                    print(f"     (exists: {exists})")
                print(f"   Product name: {item.product_name}")
                print(f"   Manufacturer: {item.manufacturer}")

            # Summary by item
            print(f"\n{'='*80}")
            print("Summary by Item")
            print(f"{'='*80}")
            items_by_key = {}
            for item in items:
                key = (item.product_id, item.variant)
                if key not in items_by_key:
                    items_by_key[key] = []
                items_by_key[key].append(item)

            print(f"Unique items: {len(items_by_key)}")
            for (product_id, variant), item_list in sorted(items_by_key.items()):
                print(f"  {product_id} + '{variant}': {len(item_list)} generation(s)")

        print(f"\n{'='*80}")
        print("[SUCCESS] LegacySource test completed successfully!")
        print(f"{'='*80}")
        return 0

    except Exception as e:
        print(f"\n[ERROR] Failed to load items: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
