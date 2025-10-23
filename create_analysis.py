report = """# VFScore Variant Identification - Comprehensive Analysis

## Summary

The VFScore codebase has a CRITICAL architectural flaw: it assumes `item_id` 
(product_id) is globally unique, but the actual data uses (product_id, variant) 
as the unique key.

IMPACT: 
- Variants are silently dropped at ingestion
- Multiple variants overwrite each other in output files
- Results are merged and ambiguous
- 4 products with variants are incorrectly processed

## Products With Multiple Variants in Dataset

- 188368: 2 variants (different algorithms)
- 335888: 1 named variant (curved-backrest)
- 369578: 2 variants (mixed)
- 558736: 2 variants (different algorithms)

## Critical Issues by Module

### ingest.py (Lines 40-121)

ISSUE: scan_generated() keeps only first GLB file
- Line 59: `gens_map[item_id] = glb_files[0]` (only first kept!)
- Multiple variants silently dropped with warning only
- Result: PERMANENT DATA LOSS

### preprocess_gt.py (Lines 56-62)

ISSUE: Directory structure uses item_id only
- Output: outputs/preprocess/refs/558736/gt_1.png
- Expected: outputs/preprocess/refs/558736/variant/gt_1.png
- Result: Variants overwrite each other

### render_cycles.py (Lines 184-190)

ISSUE: Same directory structure collapse
- Output: outputs/preprocess/cand/558736/candidate.png
- Result: Rendered images overwrite for multiple variants

### packetize.py (Lines 32-88)

ISSUE 1: Packet JSON missing variant field
- No way to distinguish which variant in packet

ISSUE 2: Directory lookup assumes single variant
- Function tries to find images in item_id folder only
- Fails if variant subdirectories exist

### scoring.py (Lines 131-225)

ISSUE: Directory structure collision
- Output: outputs/llm_calls/gemini/558736/batch_*/
- Multiple variants share same parent directory
- Result: Scoring results overwrite for variants

### aggregate.py (Lines 163-286)

ISSUE 1: aggregate_item() takes item_id only
- Function signature: def aggregate_item(item_id: str, ...)
- Cannot handle variants

ISSUE 2: Results merging
- Manifest enrichment uses item_id only
- Multiple variants get identical l1/l2/l3 values
- CSV output has no variant column

### report.py (Lines 355-360)

ISSUE: Image loading uses item_id folder
- Fails to find images if variant subdirectories exist
- Report incomplete for multi-variant products

## Required Changes

### Data Model Changes

1. manifest.jsonl: Add fields: product_id, variant, composite item_id
2. Packets: Add fields: product_id, variant, composite item_id
3. Results CSV: Add columns: product_id, variant

### File Structure Changes

Current: outputs/preprocess/refs/558736/gt_*.png
Required: outputs/preprocess/refs/558736/default/gt_*.png

All directories must include variant subdirectory:
- outputs/preprocess/refs/{product_id}/{variant}/
- outputs/preprocess/cand/{product_id}/{variant}/
- outputs/labels/{product_id}/{variant}/
- outputs/llm_calls/{model}/{product_id}/{variant}/

### Module Changes

| Module | Lines | Action |
|--------|-------|--------|
| ingest.py | 40-121 | Extract variants, add to manifest, handle multiple files |
| preprocess_gt.py | 56-62 | Add variant to path |
| render_cycles.py | 184-190 | Add variant to path |
| packetize.py | 32-88 | Add variant to packet and paths |
| scoring.py | 131-225 | Add variant to context and paths |
| aggregate.py | 163-286 | Change signature, add variant handling |
| report.py | 355-360 | Update image paths for variant |

## Severity

CRITICAL - Pipeline cannot correctly handle multi-variant products

## Files to Review

/c/Users/Shadow/Tools/VFScore/src/vfscore/ingest.py
/c/Users/Shadow/Tools/VFScore/src/vfscore/preprocess_gt.py
/c/Users/Shadow/Tools/VFScore/src/vfscore/render_cycles.py
/c/Users/Shadow/Tools/VFScore/src/vfscore/packetize.py
/c/Users/Shadow/Tools/VFScore/src/vfscore/scoring.py
/c/Users/Shadow/Tools/VFScore/src/vfscore/aggregate.py
/c/Users/Shadow/Tools/VFScore/src/vfscore/report.py
"""

with open('VARIANT_ANALYSIS.md', 'w') as f:
    f.write(report)

print("Analysis written to VARIANT_ANALYSIS.md")
