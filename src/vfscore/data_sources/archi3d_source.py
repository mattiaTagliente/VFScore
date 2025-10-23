"""
Archi3D data source for VFScore.

Reads from archi3D's Single Source of Truth database:
  - tables/items.csv (catalog of items with metadata)
  - tables/generations.csv (generation records)

All paths are workspace-relative as per archi3D conventions.
"""

import csv
from pathlib import Path
from typing import Iterator, List, Dict, Tuple, Set
from .base import ItemRecord


class Archi3DSource:
    """
    Data source for archi3D integration pipeline.

    Reads items and generations from archi3D's workspace database tables.
    Expects workspace-relative paths as per archi3D conventions.

    Args:
        workspace: Path to archi3D workspace root
        run_id: Optional run_id to filter generations (e.g., "2025-08-17_v1")
        items_csv: Optional override for items CSV path (defaults to tables/items.csv)
        generations_csv: Optional override for generations CSV path (defaults to tables/generations.csv)
    """

    def __init__(
        self,
        workspace: Path,
        run_id: str | None = None,
        items_csv: Path | None = None,
        generations_csv: Path | None = None,
    ):
        self.workspace = Path(workspace)
        self.run_id = run_id

        # Default table paths
        self.items_csv = Path(items_csv) if items_csv else self.workspace / "tables" / "items.csv"
        self.generations_csv = Path(generations_csv) if generations_csv else self.workspace / "tables" / "generations.csv"

        # Validate inputs
        if not self.workspace.exists():
            raise FileNotFoundError(f"Workspace not found: {self.workspace}")

        if not self.items_csv.exists():
            raise FileNotFoundError(f"Items CSV not found: {self.items_csv}")

        if not self.generations_csv.exists():
            raise FileNotFoundError(f"Generations CSV not found: {self.generations_csv}")

    def load_items(self) -> Iterator[ItemRecord]:
        """
        Load items from archi3D data source.

        Steps:
        1. Read tables/items.csv to get item catalog with metadata
        2. Read tables/generations.csv to get generation records
        3. Filter generations by run_id if specified
        4. Match generations to items by (product_id, variant)
        5. Resolve reference image paths from item source_folder
        6. Yield ItemRecord for each generation

        Yields:
            ItemRecord: Individual generation records with metadata
        """
        # Step 1: Read items catalog
        print(f"[Archi3DSource] Reading items catalog: {self.items_csv}")
        items_catalog = self._read_items_csv()
        print(f"[Archi3DSource] Found {len(items_catalog)} items in catalog")

        # Step 2: Read generations
        print(f"[Archi3DSource] Reading generations: {self.generations_csv}")
        generation_records = self._read_generations_csv()
        print(f"[Archi3DSource] Found {len(generation_records)} generation records")

        # Step 3: Filter by run_id if specified
        if self.run_id:
            print(f"[Archi3DSource] Filtering by run_id: {self.run_id}")
            generation_records = [
                rec for rec in generation_records
                if rec['run_id'] == self.run_id
            ]
            print(f"[Archi3DSource] After filtering: {len(generation_records)} records")

        # Step 4-6: Match, resolve paths, and yield ItemRecords
        print("[Archi3DSource] Creating ItemRecords...")
        yielded_count = 0
        skipped_no_item = 0
        skipped_no_refs = 0
        skipped_no_glb = 0

        for gen_rec in generation_records:
            product_id = gen_rec['product_id']
            variant = gen_rec['variant']
            item_key = (product_id, variant)

            # Get item metadata from catalog
            item_metadata = items_catalog.get(item_key)
            if not item_metadata:
                skipped_no_item += 1
                print(f"[WARNING] Item not found in catalog: {product_id} + variant '{variant}'")
                continue

            # Get reference images from item source_folder
            ref_image_paths = self._get_reference_images(item_metadata['source_folder'])
            if not ref_image_paths:
                skipped_no_refs += 1
                print(f"[WARNING] No reference images found for {product_id} + variant '{variant}'")
                continue

            # Resolve GLB path (workspace-relative)
            glb_path = self._resolve_glb_path(gen_rec['output_glb_relpath'])
            if not glb_path or not glb_path.exists():
                skipped_no_glb += 1
                print(f"[WARNING] GLB file not found: {gen_rec['output_glb_relpath']}")
                continue

            # Create item_id (composite identifier)
            item_id = f"{product_id}_{variant}" if variant else product_id

            # Create ItemRecord
            record = ItemRecord(
                product_id=product_id,
                variant=variant,
                item_id=item_id,
                ref_image_paths=ref_image_paths,
                glb_path=glb_path,
                algorithm=gen_rec['algorithm'],
                job_id=gen_rec['job_id'],
                product_name=item_metadata.get('product_name'),
                manufacturer=item_metadata.get('manufacturer'),
                category_l1=item_metadata.get('category_l1'),
                category_l2=item_metadata.get('category_l2'),
                category_l3=item_metadata.get('category_l3'),
                source_type="archi3d",
            )

            yield record
            yielded_count += 1

        print(f"[Archi3DSource] Yielded {yielded_count} ItemRecords")
        if skipped_no_item > 0:
            print(f"[Archi3DSource] Skipped {skipped_no_item} records (item not in catalog)")
        if skipped_no_refs > 0:
            print(f"[Archi3DSource] Skipped {skipped_no_refs} records (no reference images)")
        if skipped_no_glb > 0:
            print(f"[Archi3DSource] Skipped {skipped_no_glb} records (GLB file not found)")

    def _read_items_csv(self) -> Dict[Tuple[str, str], Dict[str, str]]:
        """
        Read tables/items.csv and return dict mapping (product_id, variant) to metadata.

        Expected columns:
            product_id, variant, product_name, manufacturer, category_l1, category_l2,
            category_l3, source_folder

        Returns:
            Dict mapping (product_id, variant) to item metadata dict
        """
        items = {}
        with open(self.items_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                product_id = row['product_id'].strip()
                variant = row['variant'].strip()
                items[(product_id, variant)] = {
                    'product_name': row.get('product_name', '').strip(),
                    'manufacturer': row.get('manufacturer', '').strip(),
                    'category_l1': row.get('category_l1', '').strip(),
                    'category_l2': row.get('category_l2', '').strip(),
                    'category_l3': row.get('category_l3', '').strip(),
                    'source_folder': row.get('source_folder', '').strip(),
                }
        return items

    def _read_generations_csv(self) -> List[Dict[str, str]]:
        """
        Read tables/generations.csv and return list of generation records.

        Expected columns:
            run_id, job_id, product_id, variant, algorithm, n_images, duration_s,
            output_glb_relpath, worker, unit_price_usd, status

        Returns:
            List of generation record dicts
        """
        records = []
        with open(self.generations_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Only include completed generations
                status = row.get('status', '').strip().lower()
                if status != 'completed':
                    continue

                records.append({
                    'run_id': row['run_id'].strip(),
                    'job_id': row['job_id'].strip(),
                    'product_id': row['product_id'].strip(),
                    'variant': row['variant'].strip(),
                    'algorithm': row['algorithm'].strip(),
                    'n_images': row.get('n_images', ''),
                    'duration_s': row.get('duration_s', ''),
                    'output_glb_relpath': row['output_glb_relpath'].strip(),
                    'worker': row.get('worker', ''),
                    'unit_price_usd': row.get('unit_price_usd', ''),
                })
        return records

    def _get_reference_images(self, source_folder: str) -> List[Path]:
        """
        Get reference images from item source_folder.

        The source_folder is workspace-relative and contains reference images
        for this item.

        Args:
            source_folder: Workspace-relative path to source folder (e.g., "sources/335888_variant")

        Returns:
            List of absolute paths to reference images
        """
        if not source_folder:
            return []

        # Resolve workspace-relative path
        folder_path = self.workspace / source_folder

        if not folder_path.exists() or not folder_path.is_dir():
            return []

        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        image_paths = [
            img_path for img_path in folder_path.iterdir()
            if img_path.is_file() and img_path.suffix.lower() in image_extensions
        ]

        return sorted(image_paths)

    def _resolve_glb_path(self, glb_relpath: str) -> Path | None:
        """
        Resolve GLB file path from workspace-relative path.

        Args:
            glb_relpath: Workspace-relative path (e.g., "generations/2025-08-17_v1/335888_variant/model.glb")

        Returns:
            Absolute Path to GLB file, or None if cannot be resolved
        """
        if not glb_relpath:
            return None

        # Resolve workspace-relative path
        glb_path = self.workspace / glb_relpath

        return glb_path if glb_path.exists() else None

    def get_source_info(self) -> dict:
        """Return metadata about this data source."""
        return {
            "type": "archi3d",
            "workspace": str(self.workspace),
            "run_id": self.run_id,
            "items_csv": str(self.items_csv),
            "generations_csv": str(self.generations_csv),
        }
