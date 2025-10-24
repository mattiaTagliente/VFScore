# VFScore Validation Study - Complete Guide

**Version**: 1.0.0
**Last Updated**: January 2025

A comprehensive guide for running validation studies, understanding statistical metrics, and interpreting results.

---

## Table of Contents

- [Introduction](#introduction)
- [Setup and Prerequisites](#setup-and-prerequisites)
- [Running Validation Studies](#running-validation-studies)
- [Understanding the Metrics](#understanding-the-metrics)
- [Enhanced Validation Reports](#enhanced-validation-reports)
- [Result Analysis](#result-analysis)
- [Technical Implementation](#technical-implementation)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Introduction

### What is a Validation Study?

A validation study systematically evaluates VFScore's reliability and consistency by:

1. **Running multiple evaluations** of the same objects
2. **Sweeping across parameter settings** (temperature, top-p)
3. **Computing statistical metrics** (ICC, MAD, correlations)
4. **Comparing with human evaluations** (if available)
5. **Identifying optimal configurations** based on multi-criteria analysis

### Why Run a Validation Study?

- **Before Production**: Verify consistency before deploying to stakeholders
- **Model Comparison**: Compare different LLM models or versions
- **Parameter Optimization**: Find best temperature/top-p settings
- **Reliability Documentation**: Provide statistical evidence of system quality
- **Human Agreement**: Validate automated scoring against expert judgments

### Study Design

The default validation study evaluates:
- **9 diverse objects** (3 manufacturers × 3 categories)
- **10 parameter combinations** (1 baseline + 3×3 grid)
- **5 repeats per setting** (statistical robustness)
- **Total: 450 API calls** (~4-5 hours with Gemini free tier)

---

## Setup and Prerequisites

### Requirements

Before running validation studies, ensure:

1. **VFScore is installed and configured**:
   ```bash
   cd VFScore
   vfscore --version
   ```

2. **Pipeline prerequisites completed**:
   ```bash
   vfscore ingest           # Manifest created
   vfscore preprocess-gt    # GT images processed
   vfscore render-cand      # Candidates rendered
   vfscore package          # Scoring packets ready
   ```

3. **API credentials configured**:
   - `.env` file contains `GEMINI_API_KEY`
   - Check rate limits for your API tier

4. **Object selection ready**:
   - `selected_objects_optimized.csv` exists
   - Contains diverse, high-quality objects

### Environment Activation

Always activate the virtual environment:

```bash
# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Directory Structure

The validation study operates from the `validation_study/` subdirectory:

```
VFScore/
├── validation_study/
│   ├── validation_study.py                      # Main orchestrator
│   ├── validation_report_generator_enhanced.py  # Report generator
│   ├── selected_objects_optimized.csv           # Object selection
│   └── validation_results_<timestamp>/          # Study outputs
└── outputs/                                     # Standard VFScore outputs
    ├── llm_calls/                               # Batch results
    └── report/                                  # Standard reports
```

---

## Running Validation Studies

### Step 1: Cost Estimation (Dry Run)

Always start with a dry run to estimate costs:

```bash
cd validation_study
python validation_study.py
```

**Output**:
```
================================================================================
VALIDATION STUDY COST ESTIMATION
================================================================================
Objects: 9
Parameter settings: 10
Repeats per setting: 5
Total API calls: 450
Estimated time (free tier): 3h 45m
================================================================================

[DRY RUN] Skipping actual evaluation.
[INFO] To run the actual study, add --run flag
```

### Step 2: Run the Study

Execute the full validation study:

```bash
# With confirmation
python validation_study.py --run

# Skip confirmation
python validation_study.py --run --yes
```

**What Happens**:
1. User confirmation (unless `--yes` flag)
2. **Phase 1: Parameter Sweep**
   - Loops through 10 parameter settings
   - For each setting: scores 9 objects with 5 repeats
   - Calls `vfscore score --temperature X --top-p Y`
   - Results saved to timestamped batch directories
3. **Phase 2: Aggregation**
   - Automatically runs `vfscore aggregate`
   - Merges all batch results
   - Computes statistics (median, MAD, etc.)
4. **Phase 3: Standard Report**
   - Automatically runs `vfscore report`
   - Generates bilingual HTML report
5. **Phase 4: Validation Report**
   - Runs enhanced report generator
   - Creates statistical analysis report
   - Includes interactive charts and help

**Progress Output**:
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

### Step 3: Review Results

After completion, two reports are available:

**Standard Report**:
```bash
start outputs/report/index.html  # Windows
open outputs/report/index.html   # macOS
```

**Enhanced Validation Report**:
```bash
start validation_results_<timestamp>/validation_report.html
```

### Command-Line Options

Full options reference:

```bash
python validation_study.py [OPTIONS]

Options:
  --run              Actually run the study (default: dry run only)
  --yes              Skip confirmation prompt (auto-confirm)
  --repeats N        Number of repeats per setting (default: 5)
  --model MODEL      LLM model to use (default: gemini-2.5-pro)
  -h, --help         Show help message

Examples:
  # Quick test (2 repeats, fast model)
  python validation_study.py --run --yes --repeats 2 --model gemini-2.5-flash

  # Full study (5 repeats, best model)
  python validation_study.py --run --repeats 5 --model gemini-2.5-pro

  # Dry run only (default)
  python validation_study.py
```

---

## Understanding the Metrics

### Reliability Metrics

#### ICC (Intra-Class Correlation)

**What it measures**: Repeatability and consistency across multiple evaluations

**Formula**: Proportion of total variance due to between-item differences

**Interpretation**:
- ICC ≥ 0.90: Excellent reliability
- ICC ≥ 0.85: Good reliability
- ICC ≥ 0.70: Acceptable reliability
- ICC < 0.70: Poor reliability

**Why important**: High ICC means VFScore produces consistent scores when evaluating the same object multiple times.

#### MAD (Median Absolute Deviation)

**What it measures**: Robust measure of score dispersion

**Formula**: `MAD = median(|score_i - median(scores)|)`

**Interpretation**:
- MAD ≤ 0.05: Excellent stability (on 0-1 scale)
- MAD ≤ 0.10: Good stability
- MAD > 0.10: High variability

**Why important**: Low MAD indicates predictable, reproducible scores with minimal variance.

#### Confidence Interval (95% CI)

**What it measures**: Uncertainty range for mean score estimate

**Formula**: `CI = mean ± 1.96 × (std / √n)`

**Interpretation**: 95% probability the true mean lies within this interval

**Why important**: Narrow CI indicates high precision in score estimates.

### Human Agreement Metrics

#### Pearson Correlation

**What it measures**: Linear relationship between LLM and human scores

**Range**: -1 to +1 (0 = no relationship)

**Interpretation**:
- ρ ≥ 0.9: Very strong agreement
- ρ ≥ 0.7: Strong agreement
- ρ ≥ 0.5: Moderate agreement
- ρ < 0.5: Weak agreement

**Why important**: High Pearson correlation means LLM scores track human judgments linearly.

#### Spearman Correlation

**What it measures**: Monotonic relationship (rank-order agreement)

**Range**: -1 to +1

**Interpretation**: Same as Pearson, but for rankings rather than absolute values

**Why important**: Robust to outliers; validates that LLM and humans agree on relative quality.

#### MAE (Mean Absolute Error)

**What it measures**: Average prediction error magnitude

**Formula**: `MAE = mean(|llm_score - human_score|)`

**Interpretation**: Lower is better (0 = perfect agreement)

**Why important**: Quantifies practical accuracy of automated scoring.

#### RMSE (Root Mean Square Error)

**What it measures**: Error magnitude with emphasis on large errors

**Formula**: `RMSE = sqrt(mean((llm_score - human_score)²))`

**Interpretation**: Lower is better; always ≥ MAE

**Why important**: Penalizes large errors more than MAE.

### LLM Parameters

#### Temperature

**What it controls**: Randomness in LLM sampling

**Range**: 0.0 (deterministic) to 1.0+ (very random)

**Common values**:
- 0.0: Deterministic (always picks most likely token)
- 0.2: Low randomness (slight variation)
- 0.5: Moderate randomness
- 0.8: High randomness (more creative)

**Why it matters**: Higher temperature → more diverse outputs, but potentially less consistent.

#### Top-P (Nucleus Sampling)

**What it controls**: Cumulative probability threshold for token selection

**Range**: 0.0 to 1.0

**Common values**:
- 1.0: Consider all tokens (no filtering)
- 0.95: Consider top 95% probability mass
- 0.9: Consider top 90% probability mass

**Why it matters**: Lower top-p → more focused sampling, higher top-p → more diversity.

---

## Enhanced Validation Reports

### Report Structure

The enhanced validation report includes:

1. **Hero Section**
   - Study title (bilingual)
   - Language toggle (English | Italiano)
   - Study metadata (model, objects, settings, evaluations)

2. **Executive Summary**
   - Best ICC (reliability champion)
   - Best correlation (human agreement)
   - Lowest MAE (prediction accuracy)
   - JSON validity rate
   - Recommended configuration

3. **Parameter Sweep Results**
   - Individual cards for each setting
   - Color-coded performance badges
   - Baseline vs. test settings marked
   - Recommended setting highlighted

4. **Stability Analysis**
   - ICC bar chart (repeatability)
   - MAD line chart (dispersion trends)
   - Confidence interval visualization

5. **Human Agreement Section**
   - Pearson vs. Spearman comparison chart
   - MAE & RMSE trend analysis
   - Scatter plot (LLM vs. human scores)

6. **Data Export**
   - Download complete results (JSON)
   - Download summary table (CSV)

7. **Interactive Help System**
   - Floating help button (?)
   - Full-screen modal with concept explanations
   - Searchable content
   - Bilingual support

### Using the Report

#### Language Switching

Click the language toggle in the top-right:
- **English | Italiano**
- Preference saved in browser localStorage
- Instant switching without page reload

#### Help System

Click the floating **?** button (bottom-right) to open help:
- 7 core concepts explained
- Bilingual explanations
- Interpretation guidelines
- Practical examples

#### Data Export

Download results for further analysis:
- **Complete Results (JSON)**: All raw data
- **Summary Table (CSV)**: Metrics spreadsheet

#### Interpreting Cards

Each parameter setting card shows:
- **Setting**: Temperature and top-p values
- **ICC**: Reliability score with badge
- **MAD**: Dispersion metric
- **Correlation**: Human agreement (if available)
- **MAE/RMSE**: Prediction errors
- **CI**: Confidence interval width
- **JSON Validity**: Parsing success rate

**Color Coding**:
- 🟢 Green badges: Excellent performance
- 🟡 Yellow badges: Good performance
- 🔴 Red badges: Poor performance

---

## Result Analysis

### Batch Directory Structure

Results are stored in standard VFScore batch directories:

```
outputs/llm_calls/gemini-2.5-pro/<item_id>/
├── batch_20250123_140000_user_mattia/        # Setting 1: temp=0.0, top_p=1.0
│   ├── rep_1.json (metadata: temp, top_p, run_id)
│   ├── rep_2.json
│   ├── rep_3.json
│   ├── rep_4.json
│   ├── rep_5.json
│   └── batch_info.json (batch metadata)
├── batch_20250123_141500_user_mattia/        # Setting 2: temp=0.2, top_p=1.0
│   └── ...
└── ... (10 batches per item)
```

### Result JSON Format

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
    "Color palette closely matches reference photos...",
    "Material finish accurately represents..."
  ],
  "metadata": {
    "temperature": 0.5,
    "top_p": 0.95,
    "run_id": "a7f3c4e2-9d1b-4a8f-b6e5-3c2f1a8d9e7b",
    "timestamp": "2025-01-23T14:23:45.123456",
    "model_name": "gemini-2.5-pro"
  }
}
```

### Study Metadata

Study configuration and costs saved separately:

```
validation_results_<timestamp>/
├── config.json         # Study configuration
├── cost_estimate.json  # API cost estimation
└── validation_report.html
```

---

## Technical Implementation

### CLI Modifications (Phase 1)

VFScore's CLI has been enhanced to support parameter sweeps:

#### Added CLI Parameters

```python
# src/vfscore/__main__.py
@app.command()
def score(
    temperature: float = typer.Option(None, help="Sampling temperature"),
    top_p: float = typer.Option(None, help="Top-p sampling parameter"),
    ...
):
    ...
```

**Usage**:
```bash
vfscore score --temperature 0.5 --top-p 0.95 --repeats 5
```

#### BaseLLMClient Enhancement

```python
# src/vfscore/llm/base.py
class BaseLLMClient:
    def __init__(self, model_name: str, temperature: float = 0.0,
                 top_p: float = 1.0, run_id: str = None):
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.run_id = run_id or str(uuid.uuid4())  # Auto-generate if not provided
```

#### Run ID Nonce

Each evaluation gets a unique run_id included in the prompt:

```python
def _build_user_message(self, context, rubric_weights):
    message = f"""Context:
...
Run ID: {self.run_id}  # Ensures statistical independence

Instructions:
..."""
    return message
```

**Why**: Prevents LLM caching and ensures true statistical independence across repeated evaluations.

#### Metadata Logging

```python
# src/vfscore/llm/gemini.py
result["metadata"] = {
    "temperature": self.temperature,
    "top_p": self.top_p,
    "run_id": self.run_id,
    "timestamp": datetime.now().isoformat(),
    "model_name": self.model_name
}
```

### Validation Study Orchestrator

The `validation_study.py` script orchestrates the entire workflow:

1. **Load configuration** and object selection
2. **Calculate costs** (API calls, time estimate)
3. **Get user confirmation** (unless `--yes` flag)
4. **Parameter sweep loop**:
   - For each setting (temp, top_p):
     - For each object:
       - Call `vfscore score` with parameters
       - Save results to batch directories
5. **Automatic post-processing**:
   - Run `vfscore aggregate`
   - Run `vfscore report`
   - Generate enhanced validation report

### Enhanced Report Generator

The `validation_report_generator_enhanced.py` generates bilingual HTML reports with:

- **Bootstrap 5** for responsive layout
- **Chart.js** for interactive charts
- **Plotly** for scatter plots
- **localStorage** for language persistence
- **JSON/CSV** export functionality

**Key features**:
- No server required (standalone HTML)
- All assets embedded or CDN-linked
- Works offline (except CDN resources)
- Cross-browser compatible

---

## Advanced Usage

### Custom Parameter Grids

Modify `validation_study.py` to test custom parameter combinations:

```python
# Custom grid example
parameter_grid = [
    {"temp": 0.0, "top_p": 1.0},    # Baseline
    {"temp": 0.1, "top_p": 0.99},   # Very low temperature
    {"temp": 0.3, "top_p": 0.95},   # Low-moderate
    {"temp": 0.6, "top_p": 0.90},   # High
    # Add your custom settings
]
```

### Comparing Multiple Models

Run separate studies for different models:

```bash
# Study 1: Gemini 2.5 Pro
python validation_study.py --run --yes --model gemini-2.5-pro

# Study 2: Gemini 2.5 Flash
python validation_study.py --run --yes --model gemini-2.5-flash

# Compare results in reports
```

### Selective Object Evaluation

Test specific objects by modifying `selected_objects_optimized.csv`:

```csv
item_id,product_id,manufacturer,category_l3,vf_score,glb_filename
558736,558736,EMKO,Sedie,0.750,558736__hunyuan3d_v2p1_single_N1_a_2025-08-17_v1_h56682002.glb
# Add only the objects you want to test
```

### Manual Parameter Sweep

For maximum control, run `vfscore score` directly:

```bash
# Baseline
vfscore score --temperature 0.0 --top-p 1.0 --repeats 10

# Test setting
vfscore score --temperature 0.5 --top-p 0.95 --repeats 10

# Aggregate and report
vfscore aggregate
vfscore report
```

---

## Troubleshooting

### Common Issues

#### "vfscore: command not found"

**Cause**: Virtual environment not activated

**Solution**:
```bash
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

#### "selected_objects_optimized.csv not found"

**Cause**: CSV file missing or wrong directory

**Solution**:
1. Ensure CSV exists in `validation_study/` directory
2. Or modify `objects_csv` path in `validation_study.py`
3. Script will use mock data if not found (for demo)

#### Study runs but no results saved

**Cause**: Pipeline prerequisites not completed

**Solution**: Ensure pipeline steps completed:
```bash
vfscore ingest           # Create manifest
vfscore preprocess-gt    # Process GT images
vfscore render-cand      # Render candidates
vfscore package          # Create scoring packets
```

#### Rate limit errors during study

**Cause**: API rate limits exceeded

**Solution**:
1. Gemini client has automatic retry with exponential backoff
2. Increase interval: `GEMINI_MIN_INTERVAL_SEC=60` in `.env`
3. Use faster model: `--model gemini-2.5-flash` (higher limits)
4. Reduce repeats: `--repeats 3` instead of 5

#### "JSON parsing failed" errors

**Cause**: LLM returned malformed JSON

**Solution**:
- Normal occurrence (1-2% of responses)
- Validation study tracks JSON validity rate
- Retry logic automatically handles failures
- Check `json_validity` metric in report

#### Charts not displaying in report

**Cause**: CDN resources blocked or offline

**Solution**:
1. Check internet connection
2. Open browser console for errors
3. Disable ad-blockers temporarily
4. Use modern browser (Chrome, Firefox, Edge)

### Debugging Tips

#### Verify Single Scoring Works

Test scoring manually before running full study:

```bash
vfscore score --model gemini-2.5-pro --repeats 1
```

#### Check Batch Directories

Verify results are being saved:

```bash
ls outputs/llm_calls/gemini-2.5-pro/558736/
```

Should show multiple `batch_YYYYMMDD_HHMMSS_user_*/` directories.

#### Inspect Result Metadata

Check a result file includes metadata:

```bash
cat outputs/llm_calls/gemini-2.5-pro/558736/batch_*/rep_1.json
```

Look for `"metadata"` section with temperature, top_p, run_id.

#### Test Report Generator

Generate report from existing results:

```bash
cd validation_study
python validation_report_generator_enhanced.py
```

---

## Best Practices

### Before Running Study

1. **Complete dry run** to verify costs and time
2. **Check API credits** to avoid interruptions
3. **Test with small study** first (--repeats 2)
4. **Verify object selection** is diverse and representative
5. **Backup existing results** if reusing same objects

### During Study

1. **Monitor progress** via console output
2. **Don't interrupt** the study (no resume support)
3. **Check batch directories** periodically for results
4. **Watch for rate limit warnings** (automatic handling)
5. **Expect 4-5 hours** for full study (be patient!)

### After Study

1. **Review both reports** (standard + validation)
2. **Check recommended configuration** in validation report
3. **Export data** for external analysis if needed
4. **Document findings** for stakeholders
5. **Update VFScore config** with optimal parameters

### For Presentations

1. **Use enhanced validation report** (professional, bilingual)
2. **Toggle to Italian** if presenting to Italian stakeholders
3. **Use help system** to explain concepts to non-experts
4. **Download CSV** for including metrics in slides
5. **Highlight recommended configuration** as actionable outcome

---

## Summary

The validation study framework provides:

- ✅ **Rigorous statistical validation** of VFScore's reliability
- ✅ **Automated end-to-end workflow** from scoring to reporting
- ✅ **Bilingual, professional reports** for stakeholder presentations
- ✅ **Complete metadata tracking** for reproducibility
- ✅ **Interactive help system** for educational transparency
- ✅ **Flexible customization** for advanced users

**Next Steps**: Review [CHANGELOG.md](CHANGELOG.md) for version history and updates.

---

**Last Updated**: January 2025
**VFScore Version**: Enhanced with Validation Study Support
