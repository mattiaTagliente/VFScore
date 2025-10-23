# VFScore Architecture Analysis: Complete Data Model

## Executive Summary

**CRITICAL FINDING**: The current VFScore codebase has a fundamental architectural flaw - it assumes `product_id` uniquely identifies items, when the actual data model requires `(product_id, variant, generation_id)` for unique identification.

---

## The Complete Data Model

### Three Levels of Identification

```
1. LOGICAL ITEM (Product Variant)
   └─ Unique Key: (product_id, variant)
   └─ Example: (335888, "Curved backrest")

2. GENERATION METHOD
   └─ Unique Key: (product_id, variant, algorithm)
   └─ Example: (335888, "Curved backrest", "tripo3d_v2p5_multi")

3. INDIVIDUAL GENERATION (Actual 3D Object)
   └─ Unique Key: (product_id, variant, algorithm, job_id)
   └─ Example: (335888, "Curved backrest", "tripo3d_v2p5_multi", "8a61ab22")
   └─ Full filename: 335888_curved-backrest_tripo3d_v2p5_multi_N3_A-B-C_2025-08-17_v1_h8a61ab22.glb
```

### Data Multiplicity Examples from database.csv (802 entries)

**Example 1: Product 335888 "Curved backrest"**
- 6 different .glb files generated:
  1. tripo3d_v2p5_multi → h8a61ab22
  2. trellis_multi_multidiffusion → h7a9164db
  3. rodin_multi → h3da8edd9
  4. trellis_multi_stochastic → h020af799
  5. trellis_multi_stochastic → hd9989ca0 (SECOND RUN!)
  6. trellis_multi_multidiffusion → hedd3c989 (SECOND RUN!)

**Example 2: Product 369578 (TWO VARIANTS)**
- Variant ""  (base): 4 .glb files from 4 algorithms
- Variant "Curved backrest": 4 .glb files from 4 algorithms
- Total: 8 .glb files for this product_id

**Example 3: Product 558736**
- Variant "": 10 .glb files
  - hunyuan3d_v2_single: 2 runs (h3e6865b1, h45420771)
  - hunyuan3d_v2p1_single: 2 runs (h56682002, h72a339b0)
  - tripo3d_v2p5_single: 2 runs
  - trellis_single: 2 runs
  - tripoSR_single: 2 runs

---

## Current System Architecture (BROKEN)

### File Organization (As Implemented)

```
datasets/
├── refs/<product_id>/          ❌ WRONG - missing variant!
│   └── *.jpg                    ❌ No way to map photos to variants
└── gens/<product_id>/          ❌ WRONG - missing variant!
    └── *.glb                    ⚠️  Multiple .glb files, only first one used!
```

### Critical Bugs in Current Implementation

**1. src/vfscore/ingest.py:40-63 - DATA LOSS**
```python
def scan_generated(gens_dir: Path) -> Dict[str, Path]:
    gens_map = {}
    for item_dir in gens_dir.iterdir():
        item_id = item_dir.name  # ❌ Only product_id, no variant!
        glb_files = list(item_dir.glob("*.glb"))

        if len(glb_files) > 1:
            console.print(f"[yellow]Warning:[/yellow] Multiple .glb files...")

        gens_map[item_id] = glb_files[0]  # ❌ ONLY FIRST FILE KEPT!
    return gens_map
```

**Impact**: For product_id 558736 with 2 .glb files, one is randomly discarded!

**2. All Pipeline Modules - Missing Variant Handling**

| Module | Line | Issue |
|--------|------|-------|
| ingest.py | 27, 51 | Uses `item_id` as dict key (loses variants) |
| preprocess_gt.py | 58 | Output dir: `out_dir / item_id` (variants overwrite) |
| render_cycles.py | 187 | Output dir: `out_dir / item_id` (variants overwrite) |
| packetize.py | 71 | Packet JSON missing variant field |
| scoring.py | 150 | Results dir: `llm_calls / model / item_id` (variants overwrite) |
| aggregate.py | 201 | Takes only `item_id` parameter |
| report.py | 358 | Image paths use `item_id` only |

---

## Required Data Structure

### Proper File Organization

```
datasets/
├── refs/
│   ├── <product_id>/
│   │   ├── <variant>/           # NEW: Variant subdirectory
│   │   │   ├── photo_A.jpg
│   │   │   └── photo_B.jpg
│   │   └── default/             # For variant="" use "default"
│   │       ├── photo_A.jpg
│   │       └── photo_B.jpg
│   │
└── gens/
    └── <product_id>/
        ├── <variant>/           # NEW: Variant subdirectory
        │   ├── algo1_jobid1.glb
        │   ├── algo1_jobid2.glb  # Multiple generations allowed!
        │   └── algo2_jobid1.glb
        └── default/
            └── *.glb
```

### Example for Product 369578

```
datasets/
├── refs/369578/
│   ├── default/
│   │   ├── 369578_lisa-garden-chair_A.jpg
│   │   └── 369578_lisa-garden-chair_B.jpg
│   └── curved-backrest/
│       ├── 369578_LISA-WATERPROOF_A.jpg
│       └── 369578_LISA-WATERPROOF_B.jpg
│
└── gens/369578/
    ├── default/
    │   ├── 369578__tripo3d_v2p5_multi_..._h8705869c.glb
    │   ├── 369578__trellis_multi_..._ha1adfa5a.glb
    │   ├── 369578__rodin_multi_..._h4e5790a0.glb
    │   └── 369578__trellis_multi_stochastic_..._h8395e7a2.glb
    └── curved-backrest/
        ├── 369578_curved-backrest_tripo3d_..._h6c95905d.glb
        ├── 369578_curved-backrest_trellis_..._ha80449e7.glb
        ├── 369578_curved-backrest_rodin_..._h25fd3e46.glb
        └── 369578_curved-backrest_trellis_..._hafed3e1c.glb
```

---

## Updated Data Model

### Manifest Entry Structure (UPDATED)

```json
{
  "product_id": "369578",
  "variant": "curved-backrest",
  "item_id": "369578_curved-backrest",  // Composite key
  "ref_paths": [
    "datasets/refs/369578/curved-backrest/photo_A.jpg",
    "datasets/refs/369578/curved-backrest/photo_B.jpg"
  ],
  "glb_files": [  // ❗ CHANGED: Array instead of single path
    {
      "path": "datasets/gens/369578/curved-backrest/369578_curved-backrest_tripo3d_..._h6c95905d.glb",
      "algorithm": "tripo3d_v2p5_multi",
      "job_id": "6c95905d",
      "hash": "h6c95905d"
    },
    {
      "path": "datasets/gens/369578/curved-backrest/369578_curved-backrest_rodin_..._h25fd3e46.glb",
      "algorithm": "rodin_multi",
      "job_id": "25fd3e46",
      "hash": "h25fd3e46"
    }
  ],
  "n_refs": 2,
  "n_glbs": 4,
  "l1": "Outdoor",
  "l2": "Arredo Giardino",
  "l3": "Sgabelli da giardino"
}
```

### Composite Item ID Format

```python
def make_item_id(product_id: str, variant: str) -> str:
    """Create composite item_id from product_id and variant."""
    if not variant or variant.strip() == "":
        return product_id  # For empty variant, just use product_id
    # Normalize variant: lowercase, replace spaces with hyphens
    variant_normalized = variant.lower().replace(" ", "-")
    return f"{product_id}_{variant_normalized}"

# Examples:
make_item_id("335888", "Curved backrest") → "335888_curved-backrest"
make_item_id("369578", "")                → "369578"
make_item_id("558736", "")                → "558736"
```

---

## Required Changes by Module

### 1. src/vfscore/ingest.py

**Changes needed:**
- Update `scan_references()` to return `Dict[(product_id, variant), List[Path]]`
- Update `scan_generated()` to return `Dict[(product_id, variant), List[GlbInfo]]`
- Add filename parsing to extract variant from .glb filenames
- Update manifest structure to include all generations

```python
# NEW: Parse GLB filename to extract metadata
def parse_glb_filename(filename: str) -> dict:
    """
    Parse: 335888_curved-backrest_tripo3d_v2p5_multi_N3_A-B-C_2025-08-17_v1_h8a61ab22.glb
    """
    parts = filename.stem.split('_')
    product_id = parts[0]

    # Find variant (between product_id and algorithm)
    # Algorithms: tripo3d, trellis, rodin, hunyuan3d, tripoSR
    algo_keywords = ['tripo3d', 'trellis', 'rodin', 'hunyuan3d', 'triposr']

    variant_parts = []
    for i, part in enumerate(parts[1:], 1):
        if any(keyword in part.lower() for keyword in algo_keywords):
            break
        variant_parts.append(part)

    variant = '-'.join(variant_parts) if variant_parts else ""

    # Extract hash (last part starting with 'h')
    hash_part = [p for p in parts if p.startswith('h')][-1]
    job_id = hash_part[1:]  # Remove 'h' prefix

    return {
        'product_id': product_id,
        'variant': variant,
        'job_id': job_id,
        'filename': filename
    }
```

### 2. src/vfscore/preprocess_gt.py

**Changes needed:**
- Update to process each `(product_id, variant)` separately
- Output structure: `outputs/preprocess/refs/<product_id>/<variant>/gt_*.png`

### 3. src/vfscore/render_cycles.py

**Changes needed:**
- Update to render each .glb file separately (handle multiple per variant)
- Output structure: `outputs/rendered/<product_id>/<variant>/<job_id>_cand_*.png`

### 4. src/vfscore/packetize.py

**Changes needed:**
- Create one packet per .glb file (not per variant!)
- Packet includes: product_id, variant, job_id, algorithm
- Output: `outputs/labels/<product_id>/<variant>/<job_id>/packet.json`

### 5. src/vfscore/scoring.py

**Changes needed:**
- Accept product_id, variant, job_id parameters
- Results directory: `outputs/llm_calls/<model>/<product_id>/<variant>/<job_id>/batch_*/`

### 6. src/vfscore/aggregate.py

**Changes needed:**
- Aggregate by (product_id, variant)
- Can aggregate across job_ids to get statistics per variant
- Or keep separate results per generation

### 7. src/vfscore/report.py

**Changes needed:**
- Display hierarchy: Product → Variants → Generations
- Allow filtering/grouping by variant or algorithm

---

## Migration Strategy

### Option A: Full Reorganization (Recommended for Clean Slate)

1. Create new directory structure with variant subdirectories
2. Write migration script to reorganize existing files:
   - Parse .glb filenames to extract variant
   - Create variant subdirectories
   - Move files to correct locations
   - For ref photos: need manual mapping or heuristics

### Option B: Metadata-Based (Minimal Changes)

1. Keep current directory structure
2. Add `_metadata.json` files in each directory:
   ```json
   {
     "product_id": "369578",
     "generations": [
       {
         "glb_file": "369578__tripo3d_..._h8705869c.glb",
         "variant": "",
         "ref_photos": ["photo_A.jpg", "photo_B.jpg"]
       },
       {
         "glb_file": "369578_curved-backrest_rodin_..._h25fd3e46.glb",
         "variant": "curved-backrest",
         "ref_photos": ["photo_C.jpg", "photo_D.jpg"]
       }
     ]
   }
   ```
3. Update code to read metadata files

### Option C: Database-Driven (Most Robust)

1. Use `database.csv` as source of truth
2. Code reads database to understand:
   - Which .glb files exist
   - Which variant each belongs to
   - Which ref photos were used (from n_images column)
3. Advantages:
   - Single source of truth
   - Handles all 802 generations properly
   - Can filter/select subsets for validation studies

---

## Current Datasets Analysis

Based on files in `datasets/`:

| Product | Variants | # GLBs | # Refs | Issue |
|---------|----------|--------|--------|-------|
| 188368 | "" | 2 | 1 | 2 generations, same variant |
| 335888 | "curved-backrest" | 1 | 3 | ✓ OK |
| 369578 | "", "curved-backrest" | 2 | 4 | Which refs for which variant? |
| 389010 | "" | 1 | 2 | ✓ OK |
| 451898 | "75-cm" | 1 | 1 | ✓ OK |
| 558736 | "" | 2 | 2 (1 dup) | 2 generations, same variant |
| 599336 | "" | 1 | 2 | ✓ OK |
| 709360 | "" | 1 | 3 | ✓ OK |
| 737048 | "" | 1 | 3 | ✓ OK |

**Total**: 9 unique product_ids, 11 unique (product_id, variant) pairs, 12 .glb files

---

## Recommended Solution

### For Your Validation Study

Given that `selected_objects_optimized.csv` already specifies which specific .glb files to evaluate, the simplest approach is:

**1. Use database.csv + selected_objects_optimized.csv as Master Index**

```python
# Load selected objects
selected = pd.read_csv('selected_objects_optimized.csv')

for _, row in selected.iterrows():
    product_id = row['product_id']
    variant = row['variant'] if pd.notna(row['variant']) else ""
    glb_filename = row['3D Object filename']

    # Find entry in database.csv
    db_entry = database[database['output_glb_relpath'].str.contains(glb_filename)]
    n_images = db_entry['n_images'].values[0]

    # Now you know exactly which .glb and how many ref images were used
```

**2. For Reference Photos Mapping**

Since the database doesn't store which specific photos were used, you need heuristics:

```python
def map_refs_to_variant(product_id: str, variant: str, n_images: int,
                        all_ref_photos: List[Path]) -> List[Path]:
    """
    Heuristic mapping of ref photos to variants.

    Strategy:
    - If variant is empty, use first n_images photos (sorted)
    - If variant is specified, look for photos with variant keywords in filename
    - Fallback: use first n_images photos
    """
    variant_keywords = variant.lower().replace('-', ' ').split()

    # Try to find photos matching variant
    matching = []
    for photo in all_ref_photos:
        if any(kw in photo.name.lower() for kw in variant_keywords):
            matching.append(photo)

    if len(matching) >= n_images:
        return sorted(matching)[:n_images]

    # Fallback: use first n_images
    return sorted(all_ref_photos)[:n_images]
```

**3. Update Ingest to be Database-Driven**

```python
def run_ingest_from_database(config: Config, database_path: Path,
                              selected_objects_path: Path) -> Path:
    """
    Ingest using database.csv and selected_objects_optimized.csv as source of truth.
    """
    import pandas as pd

    database = pd.read_csv(database_path)
    selected = pd.read_csv(selected_objects_path)

    manifest_records = []

    for _, row in selected.iterrows():
        product_id = str(row['product_id'])
        variant = row['variant'] if pd.notna(row['variant']) else ""
        glb_filename = row['3D Object filename']

        # Find .glb file in datasets
        item_id = make_item_id(product_id, variant)
        glb_path = find_glb_file(config.paths.gens_dir, glb_filename)

        # Find ref photos
        ref_dir = config.paths.refs_dir / product_id
        all_refs = sorted(list(ref_dir.glob("*.jpg")) + list(ref_dir.glob("*.png")))

        # Get n_images from database
        db_entry = database[database['output_glb_relpath'].str.contains(glb_filename)]
        n_images = int(db_entry['n_images'].values[0])

        # Map refs to this variant
        ref_paths = map_refs_to_variant(product_id, variant, n_images, all_refs)

        record = {
            "product_id": product_id,
            "variant": variant,
            "item_id": item_id,
            "glb_path": str(glb_path),
            "glb_filename": glb_filename,
            "ref_paths": [str(p) for p in ref_paths],
            "n_refs": len(ref_paths),
            # ... other fields
        }

        manifest_records.append(record)

    # Write manifest
    manifest_path = config.paths.out_dir / "manifest.jsonl"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        for record in manifest_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    return manifest_path
```

---

## Implementation Effort

| Task | Effort | Priority |
|------|--------|----------|
| Update ingest.py to use database.csv | 2-3 hours | HIGH |
| Add variant support to all modules | 6-8 hours | HIGH |
| Update output directory structures | 2-3 hours | HIGH |
| Update manifest format | 1-2 hours | HIGH |
| Ref photo mapping heuristics | 2-3 hours | MEDIUM |
| Testing with full database.csv | 4-5 hours | MEDIUM |
| Documentation updates | 2-3 hours | LOW |

**Total: ~20-27 hours**

---

## Next Steps

1. **Immediate**: Fix validation_study.py to use database-driven ingest
2. **Short-term**: Add variant support to manifest and critical modules
3. **Long-term**: Reorganize file structure with variant subdirectories
4. **Documentation**: Update GUIDE.md and CLAUDE.md with new data model

---

## Conclusion

The current architecture cannot properly handle your data due to:
1. Missing variant dimension
2. Assumption of 1:1 mapping between product_id and .glb file
3. No support for multiple generations per (product_id, variant)

The recommended fix is to use `database.csv` and `selected_objects_optimized.csv` as the source of truth and update the ingest module to be database-driven rather than filesystem-driven.
