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


class LegacySource:
    """
    Data source for legacy VFScore validation study data.

    Reads generation records from database.csv and reference images from
    a dataset folder where subdirectories are named with the pattern:
    <product_id>_<variant> or just <product_id> (when variant is empty).

    Args:
        database_csv: Path to database.csv file
        dataset_folder: Path to folder containing reference image subdirectories
        selected_objects_csv: Optional path to CSV file that filters which items to include
        vfscore_root: Root path of VFScore project (for resolving relative GLB paths)
    """

    def __init__(
        self,
        database_csv: Path,
        dataset_folder: Path,
        selected_objects_csv: Path | None = None,
        vfscore_root: Path | None = None,
    ):
        self.database_csv = Path(database_csv)
        self.dataset_folder = Path(dataset_folder)
        self.selected_objects_csv = Path(selected_objects_csv) if selected_objects_csv else None
        self.vfscore_root = Path(vfscore_root) if vfscore_root else Path.cwd()

        # Validate inputs
        if not self.database_csv.exists():
            raise FileNotFoundError(f"Database CSV not found: {self.database_csv}")

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

            # Create item_id (composite identifier)
            item_id = f"{product_id}_{variant}" if variant else product_id

            # Get GLB path
            glb_path = self._resolve_glb_path(product_id, variant, gen_rec['job_id'])
            if not glb_path or not glb_path.exists():
                skipped_no_glb += 1
                print(f"[WARNING] GLB file not found for {item_id}, job_id {gen_rec['job_id'][:8]}")
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

    def _resolve_glb_path(self, product_id: str, variant: str, job_id: str) -> Path | None:
        """
        Resolve GLB file path by searching in datasets/gens directory.

        GLB files are stored in datasets/gens/<item_id>/ with filenames containing
        a hash prefix 'h' followed by the first 8 characters of the job_id.

        Example:
            product_id: "188368"
            variant: ""
            job_id: "00d888f74e16a2f3cdfe2e17ea6dc7fd946efe93"
            → Searches in: datasets/gens/188368/
            → Matches filename containing: "_h00d888f7.glb"

        Args:
            product_id: Product identifier
            variant: Variant name (can be empty)
            job_id: Full job_id hash from database

        Returns:
            Absolute Path to GLB file, or None if not found
        """
        if not job_id:
            return None

        # Compute item_id
        item_id = f"{product_id}_{variant}" if variant else product_id

        # Look in datasets/gens/<item_id>/ directory
        gens_dir = self.vfscore_root / "datasets" / "gens" / item_id

        if not gens_dir.exists() or not gens_dir.is_dir():
            # Try with just product_id if variant-based directory doesn't exist
            if variant:
                gens_dir = self.vfscore_root / "datasets" / "gens" / product_id
                if not gens_dir.exists() or not gens_dir.is_dir():
                    return None

        # Create search pattern: filename should contain "_h<first_8_chars_of_job_id>.glb"
        job_id_short = job_id[:8]
        search_pattern = f"_h{job_id_short}.glb"

        # Search for GLB file matching the job_id
        for glb_file in gens_dir.glob("*.glb"):
            if search_pattern in glb_file.name:
                return glb_file

        return None

    def get_source_info(self) -> dict:
        """Return metadata about this data source."""
        return {
            "type": "legacy",
            "database_csv": str(self.database_csv),
            "dataset_folder": str(self.dataset_folder),
            "selected_objects_csv": str(self.selected_objects_csv) if self.selected_objects_csv else None,
            "vfscore_root": str(self.vfscore_root),
        }
