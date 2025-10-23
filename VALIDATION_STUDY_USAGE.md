# VFScore Validation Study - Usage Guide

## Overview

The validation study framework allows you to systematically evaluate VFScore's reliability and human agreement by running parameter sweeps with complete metadata tracking.

---

## Quick Start

### 1. Cost Estimation (Dry Run - Default)

```bash
# Just estimate costs without running
python validation_study.py
```

This will show:
- Number of objects to evaluate
- Parameter settings to test
- Total API calls needed
- Estimated time

**Output**: Cost estimation only, no actual API calls made.

### 2. Run Actual Study

```bash
# Run the full validation study
python validation_study.py --run

# Skip confirmation prompt
python validation_study.py --run --yes

# Custom settings
python validation_study.py --run --repeats 3 --model gemini-2.5-flash
```

**This will (E2E automation)**:
1. Ask for confirmation (unless --yes flag used)
2. **Phase 1**: Run parameter sweep across all settings
3. Execute `vfscore score` for each combination
4. Save results to batch directories
5. **Phase 2**: Automatically aggregate all results (`vfscore aggregate`)
6. **Phase 3**: Generate standard bilingual HTML report (`vfscore report`)
7. **Phase 4**: Generate enhanced validation report with statistics
8. Log all metadata (temperature, top_p, run_id, timestamp)

**Everything is automated - no manual steps required!**

---

## Command-Line Options

```bash
python validation_study.py [OPTIONS]

Options:
  --run              Actually run the study (default: dry run only)
  --yes              Skip confirmation prompt (auto-confirm)
  --repeats N        Number of repeats per setting (default: 5)
  --model MODEL      LLM model to use (default: gemini-2.5-pro)
  -h, --help         Show help message
```

---

## What Gets Tested

### Default Parameter Grid

**Baseline** (deterministic):
- Temperature: 0.0
- Top-P: 1.0

**Test Settings** (9 combinations):
- Temperature: {0.2, 0.5, 0.8}
- Top-P: {1.0, 0.95, 0.9}

**Total**: 10 parameter combinations

### Objects Evaluated

Reads from `selected_objects_optimized.csv`:
- 9 objects (default)
- 3 manufacturers
- 3 L3 categories
- High visual fidelity scores (0.750-0.950)

### API Calls

For default settings:
- **9 objects** × **10 parameter settings** × **5 repeats** = **450 API calls**
- **Estimated time**: ~4-5 hours (Gemini free tier: 2 req/min)

---

## Where Results Are Saved

### Batch Directories

Results saved to standard VFScore batch directories:

```
outputs/llm_calls/gemini-2.5-pro/<item_id>/
├── batch_20251023_140000_user_<username>/
│   ├── rep_1.json (with metadata: temp=0.0, top_p=1.0, run_id=...)
│   ├── rep_2.json
│   ├── rep_3.json
│   ├── rep_4.json
│   ├── rep_5.json
│   └── batch_info.json (batch metadata)
├── batch_20251023_141500_user_<username>/
│   ├── rep_1.json (with metadata: temp=0.2, top_p=1.0, run_id=...)
│   └── ...
└── ...  (more batches for each parameter setting)
```

### Study Metadata

```
validation_results_<timestamp>/
├── config.json         # Study configuration
└── cost_estimate.json  # API cost estimation
```

---

## Result JSON Format

Each result file includes complete metadata:

```json
{
  "item_id": "558736",
  "score": 0.850,
  "subscores": {
    "color_palette": 0.900,
    "material_finish": 0.825,
    "texture_identity": 0.800,
    "texture_scale_placement": 0.875
  },
  "rationale": [
    "Color palette closely matches...",
    "Material finish accurately represents..."
  ],
  "metadata": {
    "temperature": 0.5,
    "top_p": 0.95,
    "run_id": "a7f3c4e2-9d1b-4a8f-b6e5-3c2f1a8d9e7b",
    "timestamp": "2025-10-23T14:23:45.123456",
    "model_name": "gemini-2.5-pro"
  }
}
```

---

## After Running Study

**No manual steps needed!** The script automatically:

1. ✅ **Aggregates all results** - All batches merged across parameter settings
2. ✅ **Generates standard report** - Bilingual HTML report at `outputs/report/index.html`
3. ✅ **Generates enhanced validation report** - Specialized report at `validation_results_<timestamp>/validation_report.html`

### What You Get

**Standard Report** (`outputs/report/index.html`):
- Item-by-item scoring results
- Bilingual support (English/Italian)
- Confidence metrics (MAD-based)
- Visual thumbnails

**Enhanced Validation Report** (`validation_results_<timestamp>/validation_report.html`):
- Parameter sweep comparison
- Statistical metrics (ICC, MAD, correlation)
- Interactive help menu with concept explanations
- English/Italian language toggle
- Recommended configuration
- Downloadable data (JSON/CSV)

### Viewing Reports

```bash
# Open standard report
start outputs/report/index.html  # Windows
open outputs/report/index.html   # macOS
xdg-open outputs/report/index.html  # Linux

# Open validation report
start validation_results_<timestamp>/validation_report.html
```

---

## Examples

### Example 1: Quick Test (2 repeats, fast model)

```bash
python validation_study.py --run --yes --repeats 2 --model gemini-2.5-flash
```

- Faster execution
- Lower cost
- Good for testing the workflow

### Example 2: Full Validation Study

```bash
python validation_study.py --run --repeats 5 --model gemini-2.5-pro
```

- 5 repeats for better statistics
- Gemini 2.5 Pro for best quality
- Will ask for confirmation

### Example 3: Dry Run Only

```bash
python validation_study.py
```

- No --run flag = dry run only
- Shows cost estimation
- No API calls made

---

## Troubleshooting

### "vfscore: command not found"

**Solution**: Activate virtual environment first:
```bash
# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### "selected_objects_optimized.csv not found"

**Solution**: The script will use mock data for demonstration. To use real objects:
1. Ensure `selected_objects_optimized.csv` exists in project root
2. Or modify `objects_csv` in the script

### Study runs but no results saved

**Solution**: Check that:
1. `vfscore score` command works: `vfscore score --help`
2. Datasets are properly set up: `vfscore ingest`
3. Scoring packets created: `vfscore package`

### Rate limit errors

**Solution**: The Gemini client automatically handles rate limiting with exponential backoff. If errors persist:
1. Set longer interval: `GEMINI_MIN_INTERVAL_SEC=60` in `.env`
2. Use smaller batches: `--repeats 3` instead of 5
3. Use `gemini-2.5-flash` (higher rate limits)

---

## Understanding the Output

### During Execution

```
================================================================================
[1/10] Running BASELINE: temp=0.0, top_p=1.0
================================================================================

  Scoring item 558736 (5 repeats)...
    [OK] Successfully scored 558736

  Scoring item 709360 (5 repeats)...
    [OK] Successfully scored 709360

================================================================================
[2/10] Running TEST_2: temp=0.2, top_p=1.0
================================================================================
...
```

### After Completion

```
================================================================================
VALIDATION STUDY COMPLETE
================================================================================
Total runs: 90
Failed runs: 0
Success rate: 100.0%

Results saved to batch directories in: outputs/llm_calls/
Study metadata saved to: validation_results_20251023_140000

================================================================================
NEXT STEPS
================================================================================
1. Aggregate results: vfscore aggregate
2. Analyze validation metrics using the collected batches
3. Generate enhanced bilingual report (see validation_report_generator_enhanced.py)
```

---

## Important Notes

### Statistical Independence

Each repeat gets a **unique run_id** (UUID) that is:
- Included in the prompt
- Prevents LLM caching
- Ensures true statistical independence

### Batch Accumulation

Results accumulate in batch directories:
- Each parameter setting creates a new batch
- Batches never overwrite each other
- All batches aggregated together for analysis

### Metadata Tracking

Every result includes:
- `temperature`: Sampling temperature used
- `top_p`: Top-p sampling parameter used
- `run_id`: Unique identifier for this evaluation
- `timestamp`: When evaluation was performed
- `model_name`: LLM model used

This enables:
- Complete provenance tracking
- Reproducibility
- Parameter sweep analysis

---

## For Archiproduct Presentation

After running the validation study:

1. **Collect Results**: All batches in `outputs/llm_calls/`
2. **Compute Metrics**: Use aggregated data for ICC, MAD, correlation
3. **Generate Report**: Use enhanced bilingual report generator
4. **Present Findings**:
   - Reliability (ICC ≥ 0.85)
   - Stability (Low MAD)
   - Human Agreement (ρ ≥ 0.7)
   - Recommended Configuration

---

## Questions?

- **Documentation**: See `PHASE1_IMPLEMENTATION_COMPLETE.md`
- **Code**: See `validation_study.py` (updated version)
- **Report**: See `validation_report_generator_enhanced.py`
- **Issues**: Check GitHub issues

---

**Last Updated**: 2025-10-23
**Status**: Ready for Production ✅
