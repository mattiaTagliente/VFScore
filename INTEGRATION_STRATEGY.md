# VFScore ↔ archi3D Integration Strategy

## Executive Summary

VFScore is a module within the larger **archi3D** project. Phases 1-6 of integration are complete, with VFScore functioning as a metrics computation step. Now we need to make VFScore **fully compatible with both data sources**:

1. **New**: archi3D's `tables/items.csv` and `tables/generations.csv` (SSOT)
2. **Legacy**: Standalone `database.csv` (for validation study with existing data)

**Key Insight**: archi3D already handles the data model correctly:
- (product_id, variant) uniquely identifies logical items ✓
- Multiple generations per (product_id, variant, algorithm) supported ✓
- Single Source of Truth architecture ✓

**The Solution**: Create a **database abstraction layer** in VFScore that can read from either source transparently.

---

## Current State Analysis

### archi3D Data Model (Phase 1-6 Complete)

**`tables/items.csv`** (Catalog - from Phase 1):
```csv
product_id,variant,manufacturer,product_name,category_l1,category_l2,category_l3,
n_images,image_1_path,image_2_path,...,gt_object_path,dataset_dir,build_time
```

**`tables/generations.csv`** (SSOT - from Phase 2+):
```csv
run_id,job_id,product_id,variant,algorithm,status,created_at,started_at,finished_at,
duration_s,worker,gen_object_path,used_image_1,used_image_2,...,
source_image_1,source_image_2,...,
fscore_chamfer,fscore_status,...,
vfscore_overall,vf_finish,vf_texture_identity,vf_texture_scale_placement,vf_status,...
```

**Key Features**:
- `product_id + variant` = logical item identity
- `job_id` = SHA1(product_id|variant|algo|image_set_hash)[:12]
- Multiple rows possible for same (product_id, variant, algo) with different runs
- Paths are **workspace-relative**

### Legacy Data Model (Current VFScore Standalone)

**`database.csv`**:
```csv
run_id,job_id,product_id,variant,algo,n_images,duration_s,output_glb_relpath,worker,
unit_price_usd,product_name,manufacturer,category_l1,category_l2,category_l3
```

**File Organization** (Current):
```
datasets/
├── refs/<product_id>/*.jpg   # ALL photos mixed (no variant separation)
└── gens/<product_id>/*.glb   # ALL .glb files mixed
```

**Problems**:
- No variant subdirectories
- Ref photos not mapped to specific variants
- VFScore ingest scans filesystem, not database
- Can't handle multiple generations properly

---

## Integration Architecture

### Database Abstraction Layer

Create `src/vfscore/data_sources/` module with unified interface:

```python
# src/vfscore/data_sources/base.py
from dataclasses import dataclass
from pathlib import Path
from typing import List, Protocol

@dataclass
class ItemRecord:
    """Unified item representation across data sources."""
    product_id: str
    variant: str                    # Empty string for default variant
    item_id: str                    # Composite: f"{product_id}_{variant or 'default'}"

    # Reference photos
    ref_image_paths: List[Path]     # Absolute paths
    n_refs: int

    # Generated object (for specific generation)
    glb_path: Path | None           # Absolute path
    glb_filename: str | None
    algorithm: str | None
    job_id: str | None

    # Metadata
    product_name: str | None
    manufacturer: str | None
    category_l1: str | None
    category_l2: str | None
    category_l3: str | None

    # Source tracking
    source_type: str                # "archi3d" or "legacy"
    run_id: str | None              # For archi3D source


class DataSource(Protocol):
    """Protocol for data source implementations."""

    def get_items(self) -> List[ItemRecord]:
        """Return all items available for scoring."""
        ...

    def get_item(self, product_id: str, variant: str = "") -> ItemRecord | None:
        """Get specific item by product_id and variant."""
        ...

    def get_generations(self, product_id: str, variant: str = "") -> List[ItemRecord]:
        """Get all generations for a (product_id, variant) pair."""
        ...
```

### Two Implementations

**1. archi3D Source** (`src/vfscore/data_sources/archi3d_source.py`):

```python
class Archi3DSource:
    """Data source reading from archi3D tables."""

    def __init__(self, workspace: Path, run_id: str | None = None):
        self.workspace = workspace
        self.run_id = run_id
        self.items_csv = workspace / "tables" / "items.csv"
        self.generations_csv = workspace / "tables" / "generations.csv"

    def get_items(self) -> List[ItemRecord]:
        """Load from generations.csv (if run_id specified) or items.csv."""
        if self.run_id:
            return self._load_from_generations()
        else:
            return self._load_from_items()

    def _load_from_generations(self) -> List[ItemRecord]:
        """Load completed generations for specified run_id."""
        import pandas as pd

        df = pd.read_csv(self.generations_csv, encoding='utf-8-sig')

        # Filter by run_id and status
        if self.run_id:
            df = df[df['run_id'] == self.run_id]
        df = df[df['status'] == 'completed']

        items = []
        for _, row in df.iterrows():
            # Get reference images (use 'used' set by default)
            ref_paths = []
            for i in range(1, 7):
                col = f'used_image_{i}'
                if col in row and pd.notna(row[col]):
                    path = self.workspace / row[col]
                    if path.exists():
                        ref_paths.append(path)

            # Get generated object
            glb_path = None
            if pd.notna(row['gen_object_path']):
                glb_path = self.workspace / row['gen_object_path']

            variant = row['variant'] if pd.notna(row['variant']) else ""
            item_id = make_item_id(row['product_id'], variant)

            items.append(ItemRecord(
                product_id=str(row['product_id']),
                variant=variant,
                item_id=item_id,
                ref_image_paths=ref_paths,
                n_refs=len(ref_paths),
                glb_path=glb_path,
                glb_filename=glb_path.name if glb_path else None,
                algorithm=row.get('algorithm'),
                job_id=row.get('job_id'),
                product_name=row.get('product_name'),
                manufacturer=row.get('manufacturer'),
                category_l1=row.get('category_l1'),
                category_l2=row.get('category_l2'),
                category_l3=row.get('category_l3'),
                source_type="archi3d",
                run_id=row.get('run_id'),
            ))

        return items
```

**2. Legacy Source** (`src/vfscore/data_sources/legacy_source.py`):

```python
class LegacySource:
    """Data source reading from standalone database.csv."""

    def __init__(self, database_csv: Path, datasets_dir: Path,
                 selected_objects_csv: Path | None = None):
        self.database_csv = database_csv
        self.datasets_dir = datasets_dir
        self.selected_objects_csv = selected_objects_csv

    def get_items(self) -> List[ItemRecord]:
        """
        Load from database.csv.

        If selected_objects_csv is provided, filter to only those items.
        Otherwise, return all entries in database.csv.
        """
        import pandas as pd

        db = pd.read_csv(self.database_csv, encoding='utf-8-sig')

        # Filter by selected_objects if provided
        if self.selected_objects_csv and self.selected_objects_csv.exists():
            selected = pd.read_csv(self.selected_objects_csv, encoding='utf-8-sig')
            # Filter database to only selected filenames
            selected_files = set(selected['3D Object filename'])
            db = db[db['output_glb_relpath'].apply(
                lambda p: Path(p).name in selected_files
            )]

        items = []
        for _, row in db.iterrows():
            product_id = str(row['product_id'])
            variant = row['variant'] if pd.notna(row['variant']) else ""
            item_id = make_item_id(product_id, variant)

            # Find .glb file
            glb_relpath = row['output_glb_relpath']
            glb_path = self._find_glb_file(Path(glb_relpath).name)

            # Find reference photos
            ref_paths = self._find_ref_photos(product_id, variant, row['n_images'])

            # Parse filename to extract job_id
            filename = Path(glb_relpath).name
            job_id = self._extract_job_id_from_filename(filename)

            items.append(ItemRecord(
                product_id=product_id,
                variant=variant,
                item_id=item_id,
                ref_image_paths=ref_paths,
                n_refs=len(ref_paths),
                glb_path=glb_path,
                glb_filename=glb_path.name if glb_path else None,
                algorithm=row.get('algo'),
                job_id=job_id,
                product_name=row.get('product_name'),
                manufacturer=row.get('manufacturer'),
                category_l1=row.get('category_l1'),
                category_l2=row.get('category_l2'),
                category_l3=row.get('category_l3'),
                source_type="legacy",
                run_id=row.get('run_id'),
            ))

        return items

    def _find_glb_file(self, filename: str) -> Path | None:
        """Find .glb file in datasets/gens by scanning subdirectories."""
        gens_dir = self.datasets_dir / "gens"
        for item_dir in gens_dir.iterdir():
            if item_dir.is_dir():
                glb_path = item_dir / filename
                if glb_path.exists():
                    return glb_path
        return None

    def _find_ref_photos(self, product_id: str, variant: str, n_images: int) -> List[Path]:
        """
        Find reference photos for this (product_id, variant).

        Strategy:
        1. Look in datasets/refs/<product_id>/ for all photos
        2. If variant specified, try to match photos with variant keywords
        3. Return first n_images photos (sorted)
        """
        refs_dir = self.datasets_dir / "refs" / product_id

        if not refs_dir.exists():
            return []

        # Get all photo files
        all_photos = []
        for ext in ['.jpg', '.jpeg', '.png']:
            all_photos.extend(refs_dir.glob(f"*{ext}"))

        # Sort lexicographically
        all_photos = sorted(all_photos)

        # If variant specified, try to match
        if variant:
            variant_keywords = variant.lower().replace('-', ' ').split()
            matching = [p for p in all_photos
                       if any(kw in p.name.lower() for kw in variant_keywords)]
            if len(matching) >= n_images:
                return matching[:n_images]

        # Fallback: return first n_images
        return all_photos[:n_images]

    @staticmethod
    def _extract_job_id_from_filename(filename: str) -> str | None:
        """
        Extract job_id (hash) from filename.

        Format: <product_id>_<variant>_<algo>_<params>_<date>_<run>_h<HASH>.glb
        Example: 335888_curved-backrest_tripo3d_v2p5_multi_N3_A-B-C_2025-08-17_v1_h8a61ab22.glb
        Returns: 8a61ab22
        """
        import re
        match = re.search(r'_h([0-9a-f]+)\.glb$', filename, re.IGNORECASE)
        return match.group(1) if match else None
```

### Updated Ingest Module

**`src/vfscore/ingest.py`** (refactored):

```python
"""Data ingestion with multi-source support."""

from pathlib import Path
from typing import List
from rich.console import Console

from vfscore.config import Config
from vfscore.data_sources.base import ItemRecord, DataSource
from vfscore.data_sources.archi3d_source import Archi3DSource
from vfscore.data_sources.legacy_source import LegacySource

console = Console()


def create_data_source(config: Config) -> DataSource:
    """
    Create appropriate data source based on configuration.

    Detection strategy:
    1. If config.data_source.type == "archi3d": Use Archi3DSource
    2. If config.data_source.type == "legacy": Use LegacySource
    3. Auto-detect: Check for archi3D workspace structure
    """
    # Explicit configuration
    if hasattr(config.data_source, 'type'):
        if config.data_source.type == "archi3d":
            return Archi3DSource(
                workspace=config.data_source.workspace,
                run_id=config.data_source.run_id
            )
        elif config.data_source.type == "legacy":
            return LegacySource(
                database_csv=config.data_source.database_csv,
                datasets_dir=config.paths.datasets_dir,
                selected_objects_csv=config.data_source.selected_objects_csv
            )

    # Auto-detect
    if _is_archi3d_workspace(config.project_root):
        console.print("[cyan]Detected archi3D workspace[/cyan]")
        return Archi3DSource(
            workspace=config.project_root,
            run_id=None  # Will use items.csv
        )
    else:
        console.print("[cyan]Using legacy database.csv source[/cyan]")
        return LegacySource(
            database_csv=config.project_root / "database.csv",
            datasets_dir=config.paths.datasets_dir,
            selected_objects_csv=config.project_root / "selected_objects_optimized.csv"
        )


def _is_archi3d_workspace(path: Path) -> bool:
    """Check if path is an archi3D workspace."""
    return (path / "tables" / "items.csv").exists() and \
           (path / "runs").exists()


def run_ingest(config: Config) -> Path:
    """Run ingestion using appropriate data source."""
    console.print("\n[bold]Running data ingestion...[/bold]")

    # Create data source
    source = create_data_source(config)

    # Load items
    items = source.get_items()
    console.print(f"Loaded {len(items)} items from {items[0].source_type if items else 'unknown'} source")

    # Create manifest
    manifest_path = config.paths.out_dir / "manifest.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    import json
    with open(manifest_path, 'w', encoding='utf-8') as f:
        for item in items:
            record = {
                "product_id": item.product_id,
                "variant": item.variant,
                "item_id": item.item_id,
                "glb_path": str(item.glb_path) if item.glb_path else None,
                "glb_filename": item.glb_filename,
                "ref_paths": [str(p) for p in item.ref_image_paths],
                "n_refs": item.n_refs,
                "algorithm": item.algorithm,
                "job_id": item.job_id,
                "product_name": item.product_name,
                "manufacturer": item.manufacturer,
                "category_l1": item.category_l1,
                "category_l2": item.category_l2,
                "category_l3": item.category_l3,
                "source_type": item.source_type,
                "run_id": item.run_id,
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    console.print(f"[green]Manifest created: {manifest_path}[/green]")

    # Print summary
    by_variant = {}
    for item in items:
        key = (item.product_id, item.variant)
        by_variant[key] = by_variant.get(key, 0) + 1

    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total items: {len(items)}")
    console.print(f"  Unique (product_id, variant) pairs: {len(by_variant)}")

    if items and items[0].source_type == "legacy":
        console.print(f"  [yellow]Note: Using legacy source - ref photo mapping is heuristic[/yellow]")

    return manifest_path
```

---

## Configuration Updates

### `config.yaml` (add new section):

```yaml
# Data source configuration
data_source:
  # Type: "archi3d" or "legacy" or "auto" (default)
  type: auto

  # For archi3D source
  workspace: null              # Path to archi3D workspace (auto-detect if null)
  run_id: null                 # Specific run to score (null = use items.csv)

  # For legacy source
  database_csv: database.csv
  selected_objects_csv: selected_objects_optimized.csv
```

### `config.local.yaml` example for archi3D:

```yaml
data_source:
  type: archi3d
  workspace: "C:/Users/matti/Politecnico di Bari(1)/B4V - Archiproducts - General/Testing"
  run_id: "2025-08-17_v1"
```

### `config.local.yaml` example for legacy (validation study):

```yaml
data_source:
  type: legacy
  database_csv: database.csv
  selected_objects_csv: selected_objects_optimized.csv
```

---

## Pipeline Updates

All other modules (preprocess, render, package, score, aggregate, report) need minor updates:

**Key Change**: Read from `manifest.jsonl` (not filesystem or database directly)

**Example for `preprocess_gt.py`**:

```python
def run_preprocess_gt(config: Config) -> None:
    """Preprocess ground truth images using manifest."""
    manifest_path = config.paths.out_dir / "manifest.jsonl"

    if not manifest_path.exists():
        raise FileNotFoundError("Manifest not found. Run 'vfscore ingest' first.")

    import json
    items = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        for line in f:
            items.append(json.loads(line))

    for item in items:
        item_id = item['item_id']
        ref_paths = [Path(p) for p in item['ref_paths']]

        # Process each reference image
        output_dir = config.paths.out_dir / "preprocess" / "refs" / item_id
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, ref_path in enumerate(ref_paths, 1):
            # ... preprocessing logic using ref_path
            pass
```

Similar updates for all other modules - they all read from manifest instead of scanning filesystem.

---

## Validation Study Workflow (Legacy Data)

**Step 1: Configure for legacy mode**

```yaml
# config.local.yaml
data_source:
  type: legacy
  database_csv: database.csv
  selected_objects_csv: selected_objects_optimized.csv
```

**Step 2: Run validation study**

```bash
python validation_study.py --run --yes
```

**Under the hood**:
1. `validation_study.py` calls `vfscore ingest`
2. Ingest detects legacy mode
3. LegacySource reads `selected_objects_optimized.csv`
4. For each selected .glb:
   - Finds file in `datasets/gens/<product_id>/`
   - Maps reference photos heuristically
   - Creates ItemRecord
5. Manifest created with all metadata
6. Pipeline runs normally (preprocess, render, package, score)

---

## archi3D Integration Workflow (New Data)

**Step 1: Configure for archi3D mode**

```yaml
# config.local.yaml
data_source:
  type: archi3d
  workspace: "path/to/Testing"
  run_id: "2025-08-17_v1"
```

**Step 2: Run from archi3D CLI**

```bash
archi3d compute vfscore --run-id "2025-08-17_v1"
```

**Under the hood**:
1. archi3D's `vfscore_adapter.py` invokes VFScore
2. VFScore ingest detects archi3D mode
3. Archi3DSource reads `tables/generations.csv` for run_id
4. For each completed generation:
   - Reads workspace-relative paths
   - Resolves to absolute paths
   - Creates ItemRecord
5. Manifest created
6. Pipeline runs
7. Results written to `runs/<run_id>/metrics/vfscore/<job_id>/`
8. VFScore adapter reads results
9. Adapter upserts to `tables/generations.csv` via Phase 0 atomic utilities

---

## Implementation Checklist

### Phase 1: Core Abstraction (3-4 hours)
- [ ] Create `src/vfscore/data_sources/` module
- [ ] Implement `base.py` with ItemRecord and DataSource protocol
- [ ] Implement `archi3d_source.py`
- [ ] Implement `legacy_source.py`
- [ ] Add `make_item_id()` utility function

### Phase 2: Ingest Refactor (2-3 hours)
- [ ] Refactor `src/vfscore/ingest.py` to use data sources
- [ ] Add auto-detection logic
- [ ] Update manifest format to include source metadata
- [ ] Add configuration schema updates

### Phase 3: Pipeline Updates (4-5 hours)
- [ ] Update `preprocess_gt.py` to read from manifest
- [ ] Update `render_cycles.py` to read from manifest
- [ ] Update `packetize.py` to read from manifest
- [ ] Update `scoring.py` to read from manifest
- [ ] Update `aggregate.py` to read from manifest
- [ ] Update `report.py` to read from manifest

### Phase 4: Testing (3-4 hours)
- [ ] Test legacy mode with `database.csv`
- [ ] Test validation study workflow
- [ ] Test archi3D mode (mock `tables/generations.csv`)
- [ ] Test auto-detection logic
- [ ] Verify manifest compatibility

### Phase 5: Documentation (2-3 hours)
- [ ] Update `CLAUDE.md` with data source architecture
- [ ] Update `GUIDE.md` with dual-source usage
- [ ] Update `CHANGELOG.md`
- [ ] Create migration guide

**Total Effort: ~15-19 hours**

---

## Benefits of This Approach

1. **Clean Separation**: Data source logic isolated from pipeline logic
2. **Single Source of Truth**: Each mode has its authoritative data source
3. **No Code Duplication**: Pipeline modules work with unified manifest format
4. **Transparent**: Modules don't need to know which source is active
5. **Extensible**: Easy to add new sources (e.g., direct database connection)
6. **Testable**: Mock data sources for unit tests
7. **Backwards Compatible**: Legacy data continues to work
8. **Future-Proof**: Ready for full archi3D integration

---

## Next Steps

1. **Immediate**: Implement database abstraction layer
2. **Short-term**: Refactor ingest and test with legacy data
3. **Medium-term**: Update all pipeline modules
4. **Long-term**: Full testing with archi3D workspace

Would you like me to start implementing the database abstraction layer?
