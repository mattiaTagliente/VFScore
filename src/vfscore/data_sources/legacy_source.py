"""
Legacy data source for VFScore.

Reads from database.csv (generation records) and scans a dataset folder
for reference images organized as <product_id>_<variant> subdirectories.
"""

import csv
import re
from pathlib import Path
from typing import Iterator, List, Dict, Tuple, Set
from .base import ItemRecord
from ..utils import make_item_id


class LegacySource:
    """
    Data source for legacy VFScore validation study data.

    Reads generation records from database.csv and reference images from
    a dataset folder where subdirectories are named with the pattern:
    <product_id>_<variant> or just <product_id> (when variant is empty).

    All paths in database.csv (output_glb_relpath) are resolved relative to base_path.
    The dataset_folder is also relative to base_path.

    Args:
        database_csv: Path to database.csv file (absolute)
        base_path: Base directory for all legacy data (e.g., Testing/)
        dataset_folder_rel: Relative path to dataset folder from base_path (e.g., "dataset")
        selected_objects_csv: Optional path to CSV file that filters which items to include
    """

    def __init__(
        self,
        database_csv: Path,
        base_path: Path,
        dataset_folder_rel: str = "dataset",
        selected_objects_csv: Path | None = None,
    ):
        self.database_csv = Path(database_csv)
        self.base_path = Path(base_path)
        self.dataset_folder = self.base_path / dataset_folder_rel
        self.selected_objects_csv = Path(selected_objects_csv) if selected_objects_csv else None

        # Validate inputs
        if not self.database_csv.exists():
            raise FileNotFoundError(f"Database CSV not found: {self.database_csv}")

        if not self.base_path.exists():
            raise FileNotFoundError(f"Base path not found: {self.base_path}")

        if not self.dataset_folder.exists():
            raise FileNotFoundError(f"Dataset folder not found: {self.dataset_folder}")

        if self.selected_objects_csv and not self.selected_objects_csv.exists():
            raise FileNotFoundError(f"Selected objects CSV not found: {self.selected_objects_csv}")

    def load_items(self) -> Iterator[ItemRecord]:
        """
        Load items from legacy data source.

        Steps:
        1. Read database.csv to get generation records
        2. Filter by selected_objects_csv if provided
        3. Scan dataset_folder for reference image directories
        4. Match generations to ref images by (product_id, variant)
        5. Yield ItemRecord for each generation

        Yields:
            ItemRecord: Individual generation records with metadata
        """
        # Step 1: Read database.csv
        print("[LegacySource] Reading database.csv...")
        generation_records = self._read_database_csv()
        print(f"[LegacySource] Found {len(generation_records)} generation records")

        # Step 2: Filter by selected objects if provided
        if self.selected_objects_csv:
            print(f"[LegacySource] Filtering by {self.selected_objects_csv.name}...")
            selected_keys = self._read_selected_objects()
            generation_records = [
                rec for rec in generation_records
                if (rec['product_id'], rec['variant']) in selected_keys
            ]
            print(f"[LegacySource] After filtering: {len(generation_records)} records")

        # Step 3: Scan dataset folder for reference images
        print(f"[LegacySource] Scanning dataset folder: {self.dataset_folder}")
        ref_images_map = self._scan_reference_images()
        print(f"[LegacySource] Found reference images for {len(ref_images_map)} items")

        # Step 4 & 5: Match and yield ItemRecords
        print("[LegacySource] Creating ItemRecords...")
        yielded_count = 0
        skipped_no_refs = 0
        skipped_no_glb = 0

        for gen_rec in generation_records:
            product_id = gen_rec['product_id']
            variant = gen_rec['variant']
            item_key = (product_id, variant)

            # Get reference images for this item
            ref_image_paths = ref_images_map.get(item_key)
            if not ref_image_paths:
                skipped_no_refs += 1
                print(f"[WARNING] No reference images found for {product_id} + variant '{variant}'")
                continue

            # Create item_id using utility function
            item_id = make_item_id(product_id, variant)

            # Get GLB path from database.csv (relative to base_path)
            glb_path = self._resolve_glb_path(gen_rec['output_glb_relpath'])
            if not glb_path or not glb_path.exists():
                skipped_no_glb += 1
                print(f"[WARNING] GLB file not found: {gen_rec['output_glb_relpath']}")
                continue

            # Create ItemRecord
            record = ItemRecord(
                product_id=product_id,
                variant=variant,
                item_id=item_id,
                ref_image_paths=ref_image_paths,
                glb_path=glb_path,
                algorithm=gen_rec['algo'],
                job_id=gen_rec['job_id'],
                product_name=gen_rec.get('product_name'),
                manufacturer=gen_rec.get('manufacturer'),
                category_l1=gen_rec.get('category_l1'),
                category_l2=gen_rec.get('category_l2'),
                category_l3=gen_rec.get('category_l3'),
                source_type="legacy",
            )

            yield record
            yielded_count += 1

        print(f"[LegacySource] Yielded {yielded_count} ItemRecords")
        if skipped_no_refs > 0:
            print(f"[LegacySource] Skipped {skipped_no_refs} records (no reference images)")
        if skipped_no_glb > 0:
            print(f"[LegacySource] Skipped {skipped_no_glb} records (GLB file not found)")

    def _read_database_csv(self) -> List[Dict[str, str]]:
        """Read database.csv and return list of generation records."""
        records = []
        with open(self.database_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append({
                    'run_id': row['run_id'],
                    'job_id': row['job_id'],
                    'product_id': row['product_id'].strip(),
                    'variant': row['variant'].strip(),
                    'algo': row['algo'].strip(),
                    'n_images': row['n_images'],
                    'duration_s': row['duration_s'],
                    'output_glb_relpath': row['output_glb_relpath'].strip(),
                    'worker': row.get('worker', ''),
                    'unit_price_usd': row.get('unit_price_usd', ''),
                    'product_name': row.get('product_name', ''),
                    'manufacturer': row.get('manufacturer', ''),
                    'category_l1': row.get('category_l1', ''),
                    'category_l2': row.get('category_l2', ''),
                    'category_l3': row.get('category_l3', ''),
                })
        return records

    def _read_selected_objects(self) -> Set[Tuple[str, str]]:
        """
        Read selected_objects_optimized.csv and return set of (product_id, variant) tuples.
        """
        selected = set()
        with open(self.selected_objects_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                product_id = row['product_id'].strip()
                variant = row.get('variant', '').strip()
                selected.add((product_id, variant))
        return selected

    def _scan_reference_images(self) -> Dict[Tuple[str, str], List[Path]]:
        """
        Scan dataset folder for reference image subdirectories.

        Expected folder structure (nested):
            dataset/
                <product_id> or <product_id> - <variant>/
                    images/
                        image1.jpg
                        image2.png
                        ...
                    gt/ (optional, for processed images)
                        ...

        Returns:
            Dict mapping (product_id, variant) to list of image paths
        """
        ref_images_map = {}
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}

        # Iterate through subdirectories in dataset folder
        for subdir in self.dataset_folder.iterdir():
            if not subdir.is_dir():
                continue

            # Parse folder name to extract product_id and variant
            product_id, variant = self._parse_folder_name(subdir.name)

            # Look for images in the "images/" subdirectory first
            images_dir = subdir / "images"
            image_paths = []

            if images_dir.exists() and images_dir.is_dir():
                image_paths = [
                    img_path for img_path in images_dir.iterdir()
                    if img_path.is_file() and img_path.suffix.lower() in image_extensions
                ]

            # If no images found, try looking directly in the product folder
            if not image_paths:
                image_paths = [
                    img_path for img_path in subdir.iterdir()
                    if img_path.is_file() and img_path.suffix.lower() in image_extensions
                ]

            if image_paths:
                ref_images_map[(product_id, variant)] = sorted(image_paths)
                print(f"  Found {len(image_paths)} images for ('{product_id}', '{variant}')")

        return ref_images_map

    def _parse_folder_name(self, folder_name: str) -> Tuple[str, str]:
        """
        Parse folder name to extract product_id and variant.

        Expected patterns:
            "335888 - Curved backrest" -> ("335888", "Curved backrest")
            "335888_curved-backrest" -> ("335888", "curved-backrest")
            "335888" -> ("335888", "")

        Args:
            folder_name: Name of the folder

        Returns:
            Tuple of (product_id, variant)
        """
        # Try to match pattern: <digits> - <variant> (space-dash-space separator)
        match = re.match(r'^(\d+)\s*-\s*(.+)$', folder_name)
        if match:
            product_id = match.group(1)
            variant = match.group(2).strip()
            return product_id, variant

        # Try to match pattern: <digits>_<variant> (underscore separator)
        match = re.match(r'^(\d+)_(.+)$', folder_name)
        if match:
            product_id = match.group(1)
            variant = match.group(2).replace('-', ' ').strip()
            return product_id, variant

        # Try pattern: just <digits> (no variant)
        match = re.match(r'^(\d+)$', folder_name)
        if match:
            product_id = match.group(1)
            return product_id, ""

        # Fallback: treat entire name as product_id with empty variant
        print(f"[WARNING] Could not parse folder name '{folder_name}', using as product_id")
        return folder_name, ""

    def _resolve_glb_path(self, glb_relpath: str) -> Path | None:
        """
        Resolve GLB file path from database.csv relative path.

        The output_glb_relpath in database.csv is relative to base_path.

        Example:
            base_path: "C:/Users/.../Testing"
            glb_relpath: "runs\\2025-08-17_v1\\outputs\\hunyuan3d_v2p1_single\\188368__...h00d888f7.glb"
            → Returns: "C:/Users/.../Testing/runs/2025-08-17_v1/outputs/hunyuan3d_v2p1_single/188368__...h00d888f7.glb"

        Args:
            glb_relpath: Relative path from database.csv (Windows-style backslashes)

        Returns:
            Absolute Path to GLB file, or None if not found
        """
        if not glb_relpath:
            return None

        # Convert Windows backslashes to forward slashes for Path compatibility
        glb_relpath_normalized = glb_relpath.replace('\\', '/')

        # Resolve relative to base_path
        glb_path = self.base_path / glb_relpath_normalized

        return glb_path if glb_path.exists() else None

    def get_source_info(self) -> dict:
        """Return metadata about this data source."""
        return {
            "type": "legacy",
            "base_path": str(self.base_path),
            "dataset_folder": str(self.dataset_folder),
            "database_csv": str(self.database_csv),
            "selected_objects_csv": str(self.selected_objects_csv) if self.selected_objects_csv else None,
        }
