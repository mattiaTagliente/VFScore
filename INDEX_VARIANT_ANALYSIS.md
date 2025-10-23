# VFScore Variant Identification Analysis - Complete Documentation

## Overview

This analysis provides a comprehensive assessment of how the VFScore codebase handles item identification and reveals critical issues with handling product variants.

## Documents in This Analysis

### 1. README_VARIANT_ANALYSIS.md (Start Here)
**Purpose**: Executive summary and quick reference
**Contents**:
- Problem statement
- List of affected products (188368, 335888, 369578, 558736)
- Critical issues by module with code examples
- Required changes summary
- Implementation priorities
- Effort estimate (~15-20 hours)
- Testing checklist

**Best for**: Project managers, developers getting started

---

### 2. VARIANT_ANALYSIS.md  
**Purpose**: Quick overview with tables
**Contents**:
- Summary of the core problem
- Products with multiple variants
- Module-by-module issues (ingest.py through report.py)
- Required changes by module
- Severity assessment
- Files to review with line numbers

**Best for**: Developers deciding which modules to fix first

---

### 3. VARIANT_FIX_REFERENCE.txt
**Purpose**: Detailed technical reference for implementation
**Contents**:
- Module-by-module implementation guide with line numbers
- Data model changes (manifest.jsonl, packets, CSV)
- File structure before/after
- Key code patterns to use
- Validation checklist
- Testing strategy
- Effort breakdown
- Risk factors

**Best for**: Developers implementing the fixes

---

### 4. VARIANT_ANALYSIS_SUMMARY.json
**Purpose**: Structured data for programmatic access
**Contents**:
- Problem summary in JSON format
- Affected modules with line references
- Products with variants
- Machine-readable for integration with tools

**Best for**: Automated analysis, CI/CD integration

---

## Quick Facts

### The Problem
```
ASSUMPTION (incorrect):  item_id is globally unique
REALITY (correct):       (product_id, variant) is the unique key
```

### Severity
**CRITICAL** - Pipeline cannot correctly handle multi-variant products

### Products Affected
- 188368: 2 variants
- 335888: 1 variant
- 369578: 2 variants
- 558736: 2 variants

### Impact
1. Variants silently dropped at ingestion
2. Output files overwrite across variants
3. Results merged and ambiguous
4. Report incomplete for multi-variant products

### Modules Requiring Changes
All 7 core pipeline modules:
1. src/vfscore/ingest.py (Lines 40-121)
2. src/vfscore/preprocess_gt.py (Lines 56-62)
3. src/vfscore/render_cycles.py (Lines 184-190)
4. src/vfscore/packetize.py (Lines 32-88)
5. src/vfscore/scoring.py (Lines 131-225)
6. src/vfscore/aggregate.py (Lines 163-286)
7. src/vfscore/report.py (Lines 355-360)

### Effort Required
- Total: ~15-20 hours
- Per-module changes: 4-8 hours
- Data model updates: 2-3 hours
- Testing: 3-4 hours

---

## How to Use This Analysis

### For Project Planning
1. Read **README_VARIANT_ANALYSIS.md** - understand the scope
2. Review **Effort Estimate** section - plan timeline
3. Check **Implementation Priority** - decide on phases

### For Implementation
1. Start with **README_VARIANT_ANALYSIS.md** - understand problem
2. Use **VARIANT_FIX_REFERENCE.txt** - module-by-module guide
3. Reference **VARIANT_ANALYSIS.md** - review all issues before coding
4. Consult code examples in **README_VARIANT_ANALYSIS.md** - key patterns

### For Testing
1. Review **Testing Checklist** in **README_VARIANT_ANALYSIS.md**
2. Use **Testing Strategy** section in **VARIANT_FIX_REFERENCE.txt**
3. Test with products: 558736 (2 variants), 369578 (2 variants)

### For Code Review
1. Check **Module Changes** table in **README_VARIANT_ANALYSIS.md**
2. Verify against **VARIANT_FIX_REFERENCE.txt** checklist
3. Ensure all 7 modules updated correctly
4. Validate data model changes in manifest, packets, results

---

## Key Findings Summary

### Critical Data Loss (ingest.py:59)
```python
gens_map[item_id] = glb_files[0]  # BUG: Only keeps first!
```
**Impact**: When a product has multiple GLB files (variants), only the first is kept. Others are silently dropped.

### Directory Collapse (multiple modules)
```python
output_path = base_dir / item_id / filename  # BUG: No variant subdir
```
**Impact**: All variants of same product_id use same directory, causing overwrites.

### Missing Variant Context (scoring.py)
```python
context = {"item_id": item_id, ...}  # BUG: No variant info
```
**Impact**: LLM scores items without knowing which variant is being scored.

### Result Merging (aggregate.py)
```python
manifest_record = manifest_map[item_id]  # BUG: Same record for all variants
```
**Impact**: Final results can't distinguish between variants.

---

## Solution Overview

### Data Model Changes
- manifest.jsonl: Add product_id, variant, composite item_id
- Packets: Add product_id, variant, composite item_id
- Results CSV: Add product_id, variant columns

### File Structure Changes
```
OLD: outputs/preprocess/refs/558736/gt_*.png
NEW: outputs/preprocess/refs/558736/default/gt_*.png
```

All directories must include variant subdirectory:
- outputs/preprocess/refs/{product_id}/{variant}/
- outputs/preprocess/cand/{product_id}/{variant}/
- outputs/labels/{product_id}/{variant}/
- outputs/llm_calls/{model}/{product_id}/{variant}/

### Key Code Pattern
```python
# Variant extraction
def extract_variant(filename: str, product_id: str) -> Optional[str]:
    rest = filename[len(product_id):]
    if rest.startswith("__"):
        return None  # default
    elif rest.startswith("_"):
        return rest[1:].split("_")[0]
    return None

# Composite item_id everywhere
item_id = f"{product_id}_{variant or 'default'}"

# Directory pattern
output_path = base_dir / product_id / (variant or "default") / filename
```

---

## Validation Approach

After implementation, verify:
1. All variants in manifest.jsonl
2. No file overwrites in outputs/
3. Separate scores per variant
4. Results CSV has product_id, variant columns
5. Report displays all variants
6. End-to-end test with 558736 (2 variants)

---

## Next Steps

### Phase 1: Understanding (You are here)
- Read README_VARIANT_ANALYSIS.md
- Understand the problem scope
- Review affected modules

### Phase 2: Planning
- Review VARIANT_FIX_REFERENCE.txt
- Create implementation plan
- Assign module ownership

### Phase 3: Implementation
- Start with ingest.py (critical)
- Update data models
- Update all modules systematically
- Implement comprehensive tests

### Phase 4: Validation
- Run tests with multi-variant products
- Verify outputs
- Code review
- Merge to main

---

## Questions?

Refer to the specific document:
- **"What's the problem?"** → README_VARIANT_ANALYSIS.md (Problem Statement)
- **"How long will this take?"** → README_VARIANT_ANALYSIS.md (Effort Estimate)
- **"How do I fix module X?"** → VARIANT_FIX_REFERENCE.txt (Module Changes)
- **"What are all the issues?"** → VARIANT_ANALYSIS.md (All Issues)
- **"Can I parse this data?"** → VARIANT_ANALYSIS_SUMMARY.json

---

## Files Analyzed

Primary analysis targets:
- /c/Users/Shadow/Tools/VFScore/src/vfscore/ingest.py
- /c/Users/Shadow/Tools/VFScore/src/vfscore/preprocess_gt.py
- /c/Users/Shadow/Tools/VFScore/src/vfscore/render_cycles.py
- /c/Users/Shadow/Tools/VFScore/src/vfscore/packetize.py
- /c/Users/Shadow/Tools/VFScore/src/vfscore/scoring.py
- /c/Users/Shadow/Tools/VFScore/src/vfscore/aggregate.py
- /c/Users/Shadow/Tools/VFScore/src/vfscore/report.py

Supporting analysis:
- database.csv (contains variant information)
- metadata/categories.csv (product categories)
- outputs/manifest.jsonl (current manifest structure)
- datasets/gens/ (actual file structure with variants)

---

**Analysis Created**: 2025-10-23
**Thoroughness Level**: Very Thorough
**Status**: Complete and Ready for Implementation

