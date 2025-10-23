# VFScore Variant Identification Analysis - Executive Summary

## Files Created

This analysis includes three comprehensive documents:

1. **VARIANT_ANALYSIS.md** - Quick overview of the problem and required changes
2. **VARIANT_FIX_REFERENCE.txt** - Detailed reference for implementing fixes
3. **VARIANT_ANALYSIS_SUMMARY.json** - Structured data in JSON format

## Problem Statement

The VFScore codebase assumes `item_id` is globally unique, but the actual data structure uses `(product_id, variant)` as the unique key.

### Impact

- **Variants are silently dropped** at ingestion (line 59 of ingest.py)
- **Multiple variants overwrite each other** in output files
- **Results are merged and ambiguous** - can't distinguish which variant scored what
- **4 products with variants are incorrectly processed** (188368, 335888, 369578, 558736)

## Affected Products

```
Product 188368: 2 variants (both default, different algorithms)
  - 188368__hunyuan3d_v2p1_single_N1_a_2025-08-17_v1_h00d888f7.glb
  - 188368__hunyuan3d_v2p1_single_N1_a_2025-08-17_v1_h9ee9037e.glb

Product 335888: 1 named variant
  - 335888_curved-backrest_tripo3d_v2p5_multi_N3_A-B-C_2025-08-17_v1_h8a61ab22.glb

Product 369578: 2 variants
  - 369578_curved-backrest_rodin_multi_N2_A-B_2025-08-17_v1_h25fd3e46.glb
  - 369578__trellis_multi_multidiffusion_N2_A-B_2025-08-17_v1_ha1adfa5a.glb

Product 558736: 2 variants (both default, different algorithms)
  - 558736__hunyuan3d_v2p1_single_N1_a_2025-08-17_v1_h56682002.glb
  - 558736__triposr_single_N1_a_2025-08-17_v1_hd71d2262.glb
```

## Critical Issues by Module

### ingest.py (Line 59)
```python
gens_map[item_id] = glb_files[0]  # BUG: Only keeps first!
```
- **Issue**: When multiple GLB files exist, only first is kept
- **Impact**: PERMANENT DATA LOSS - additional variants permanently dropped
- **Consequence**: 188368, 335888, 369578, 558736 lose variants

### preprocess_gt.py (Line 56-62)
```python
output_path = config.paths.out_dir / "preprocess" / "refs" / item_id / f"gt_{idx}.png"
```
- **Issue**: Directory uses item_id only (no variant)
- **Impact**: Multiple variants collapse into single folder
- **Consequence**: Files overwrite, variant data lost

### render_cycles.py (Line 184-190)
```python
output_path = config.paths.out_dir / "preprocess" / "cand" / item_id / "candidate.png"
```
- **Issue**: Same directory collapse
- **Impact**: Rendered candidates overwrite for variants

### packetize.py (Line 77-88)
```python
packet = {
    "item_id": item_id,  # BUG: No variant field
    "l1": record["l1"],
    ...
}
```
- **Issue**: Packet JSON missing variant information
- **Impact**: Downstream modules can't identify which variant

### scoring.py (Line 220-225)
```python
output_dir = base_llm_calls_dir / model_dir_name / item_id / batch_dir_name
```
- **Issue**: Multiple variants share parent directory
- **Impact**: Scoring results overwrite for variants

### aggregate.py (Line 163, 263-286)
```python
def aggregate_item(item_id: str, ...):  # BUG: No variant parameter
```
- **Issue**: Function takes item_id only, no variant handling
- **Impact**: Results merged across variants

### report.py (Line 355-360)
```python
item_labels_dir = labels_dir / item_id  # BUG: No variant subdir
```
- **Issue**: Images can't be found if variant subdirs exist
- **Impact**: Report incomplete for multi-variant products

## Required Changes Summary

### Data Models
- Add `product_id` field to manifest.jsonl
- Add `variant` field to manifest.jsonl  
- Create composite `item_id` = f"{product_id}_{variant or 'default'}"
- Update packet JSON structure
- Add columns to results CSV

### File Structure
```
Current:  outputs/preprocess/refs/558736/gt_*.png
Required: outputs/preprocess/refs/558736/default/gt_*.png

All directories need variant subdirectory:
- outputs/preprocess/refs/{product_id}/{variant}/
- outputs/preprocess/cand/{product_id}/{variant}/
- outputs/labels/{product_id}/{variant}/
- outputs/llm_calls/{model}/{product_id}/{variant}/
```

### Module Changes

| Module | Severity | Changes |
|--------|----------|---------|
| ingest.py | CRITICAL | Extract variants, handle multiple files, add to manifest |
| preprocess_gt.py | HIGH | Add variant to output paths |
| render_cycles.py | HIGH | Add variant to output paths |
| packetize.py | HIGH | Add variant to packets and paths |
| scoring.py | HIGH | Add variant to context and paths |
| aggregate.py | CRITICAL | Change signature, add variant support |
| report.py | MEDIUM | Update image loading paths |

## Effort Estimate

- **Per-module changes**: 4-8 hours
- **Data model updates**: 2-3 hours
- **Testing**: 3-4 hours
- **Total**: ~15-20 hours

## Implementation Priority

1. **CRITICAL - Must fix data loss**:
   - ingest.py: Handle multiple GLB files properly
   - Add product_id, variant, composite item_id to manifest

2. **HIGH - Required for correct pipeline**:
   - aggregate.py: Support variant in results
   - All modules: Add variant to directory structure

3. **MEDIUM - Support and usability**:
   - report.py: Display all variants
   - All docstrings and error messages

## Testing Checklist

After implementation:
- [ ] All variants in manifest.jsonl for multi-variant products
- [ ] No file overwrites in output directories
- [ ] Separate scores per variant
- [ ] Results CSV has product_id and variant columns
- [ ] Report displays all variants
- [ ] End-to-end test with 558736 (2 variants)

## Files to Modify

```
/c/Users/Shadow/Tools/VFScore/src/vfscore/ingest.py
/c/Users/Shadow/Tools/VFScore/src/vfscore/preprocess_gt.py
/c/Users/Shadow/Tools/VFScore/src/vfscore/render_cycles.py
/c/Users/Shadow/Tools/VFScore/src/vfscore/packetize.py
/c/Users/Shadow/Tools/VFScore/src/vfscore/scoring.py
/c/Users/Shadow/Tools/VFScore/src/vfscore/aggregate.py
/c/Users/Shadow/Tools/VFScore/src/vfscore/report.py
```

## Quick Reference for Key Pattern

**Variant Extraction**:
```python
def extract_variant(filename: str, product_id: str) -> Optional[str]:
    if not filename.startswith(product_id):
        return None
    rest = filename[len(product_id):]
    if rest.startswith("__"):
        return None  # default variant
    elif rest.startswith("_"):
        parts = rest[1:].split("_")
        return parts[0]
    return None
```

**Composite Item ID**:
```python
item_id = f"{product_id}_{variant or 'default'}"
```

**Directory Pattern**:
```python
variant_dir = variant or "default"
output_path = base_dir / product_id / variant_dir / filename
```

## Next Steps

1. Review VARIANT_FIX_REFERENCE.txt for detailed module-by-module changes
2. Start with ingest.py (critical data loss fix)
3. Update data models (manifest, packets, results)
4. Update all module directory structures
5. Implement comprehensive tests
6. Validate with multi-variant products

---

**Analysis Date**: 2025-10-23
**Severity**: CRITICAL
**Status**: Ready for implementation
