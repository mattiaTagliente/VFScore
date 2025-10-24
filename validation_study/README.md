# VFScore Validation Study Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status: Production Ready](https://img.shields.io/badge/status-production%20ready-green.svg)](https://github.com/mattiaTagliente/VFScore)

A comprehensive validation framework for systematically evaluating VFScore's reliability, stability, and human agreement through automated parameter sweeps.

---

## 🎯 Overview

The validation study framework enables rigorous statistical assessment of VFScore's visual fidelity scoring system by:

- 🔬 **Parameter Sweeps**: Systematic evaluation across temperature/top-p combinations
- 📊 **Statistical Analysis**: ICC, MAD, correlation, and confidence metrics
- 🌍 **Bilingual Reporting**: Enhanced HTML reports with English/Italian support
- 📈 **Interactive Visualizations**: Charts, scatter plots, and trend analysis
- 🎓 **Educational Tools**: Built-in help system explaining validation concepts
- 🤖 **Complete Automation**: End-to-end orchestration from scoring to report generation

**Use Case**: Validate VFScore's consistency and agreement with human evaluations before deployment to stakeholders.

---

## ✨ Key Features

### Statistical Validation
- **ICC (Intra-Class Correlation)**: Measures repeatability (target ≥ 0.85)
- **MAD (Median Absolute Deviation)**: Quantifies score dispersion
- **Confidence Intervals**: 95% CI for mean score estimates
- **Human Agreement**: Pearson & Spearman correlations (target ρ ≥ 0.7)
- **Error Metrics**: MAE and RMSE quantification

### Enhanced Reporting
- **Two Report Types**:
  - Standard pipeline reports (`vfscore report`)
  - Enhanced validation reports (parameter sweep analysis)
- **Interactive Help Menu**: Explains ICC, MAD, correlation, temperature, top-p concepts
- **Language Toggle**: Switch between English/Italian without page reload
- **Visual Charts**: ICC trends, MAD analysis, correlation scatter plots
- **Data Export**: Download complete results (JSON) and summaries (CSV)

### Complete Metadata Tracking
Every evaluation includes:
- `temperature`: Sampling temperature used
- `top_p`: Top-p sampling parameter
- `run_id`: Unique UUID preventing LLM caching
- `timestamp`: Evaluation datetime
- `model_name`: LLM model identifier

---

## 🚀 Quick Start

### 1. Setup

Ensure VFScore is installed and configured:

```bash
# From VFScore project root
cd VFScore
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Verify installation
vfscore --version
```

### 2. Estimate Cost (Dry Run)

Preview what the study will do:

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

### 3. Run Validation Study

Execute the complete study:

```bash
# With confirmation prompt
python validation_study.py --run

# Skip confirmation
python validation_study.py --run --yes

# Quick test with fewer repeats
python validation_study.py --run --yes --repeats 3 --model gemini-2.5-flash
```

The script automatically:
1. Runs parameter sweep across 10 settings
2. Scores 9 diverse objects with 5 repeats each
3. Aggregates all batch results
4. Generates standard HTML report
5. Generates enhanced validation report with statistics

**No manual steps required!**

### 4. View Results

```bash
# Open standard report
start outputs/report/index.html  # Windows
open outputs/report/index.html   # macOS

# Open enhanced validation report
start validation_results_<timestamp>/validation_report.html
```

---

## 📖 Documentation

- **[Complete Guide](GUIDE.md)** - Detailed usage, configuration, and analysis
- **[Changelog](CHANGELOG.md)** - Version history and updates

---

## 🎨 Usage Examples

### Example 1: Quick Test Run

Fast validation with minimal API calls:

```bash
python validation_study.py --run --yes --repeats 2 --model gemini-2.5-flash
```

- 9 objects × 10 settings × 2 repeats = **180 API calls**
- Estimated time: **~90 minutes**
- Good for testing workflow

### Example 2: Full Validation Study

Comprehensive validation for production:

```bash
python validation_study.py --run --repeats 5 --model gemini-2.5-pro
```

- 9 objects × 10 settings × 5 repeats = **450 API calls**
- Estimated time: **~4-5 hours**
- Provides robust statistics

### Example 3: Custom Parameter Grid

Use VFScore CLI directly for custom parameter combinations:

```bash
# Score with custom parameters
vfscore score --model gemini-2.5-pro --repeats 5 --temperature 0.3 --top-p 0.92

# More deterministic scoring
vfscore score --temperature 0.0 --top-p 1.0 --repeats 10

# More diverse scoring
vfscore score --temperature 0.8 --top-p 0.9 --repeats 5
```

---

## 📊 What Gets Evaluated

### Default Parameter Grid

**Baseline** (deterministic):
- Temperature: 0.0
- Top-P: 1.0

**Test Grid** (9 combinations):
- Temperature: {0.2, 0.5, 0.8}
- Top-P: {1.0, 0.95, 0.9}

**Total**: 10 parameter combinations

### Object Selection

The study uses 9 carefully selected objects (`selected_objects_optimized.csv`):

- **3 unique manufacturers** (LEOLUX LX, EMKO, S-CAB)
- **3 L3 categories** (Poltrone, Sedie, Sedie da giardino)
- **VF score range**: 0.750 - 0.950 (high-quality objects)
- **7 unique products** (some with multiple generations)

This ensures diversity across manufacturers, categories, and quality levels.

---

## 📁 File Structure

```
validation_study/
├── README.md                                    # This file
├── GUIDE.md                                     # Comprehensive guide
├── CHANGELOG.md                                 # Version history
├── validation_study.py                          # Main orchestrator
├── validation_report_generator_enhanced.py      # Enhanced report generator
├── selected_objects_optimized.csv               # Object selection
└── validation_results_<timestamp>/              # Study outputs
    ├── validation_report.html                   # Enhanced report
    ├── config.json                              # Study configuration
    └── cost_estimate.json                       # API cost info
```

---

## 🔍 Two Report Types Explained

### Standard Pipeline Report

**Purpose**: Show individual item scores from normal VFScore usage

**Generated by**: `vfscore report` command (uses `src/vfscore/report.py`)

**Features**:
- Item-by-item results
- Bilingual support (English/Italian)
- MAD-based confidence metrics
- Visual thumbnails

**Usage**: Automatic during `vfscore run-all` or `vfscore report`

**Location**: `outputs/report/index.html`

### Enhanced Validation Report

**Purpose**: Compare parameter sweep results for validation studies

**Generated by**: `validation_report_generator_enhanced.py` (manual use)

**Features**:
- Parameter sweep comparison
- Statistical metrics (ICC, MAD, correlation)
- Interactive help menu (concepts explained)
- Recommended configuration
- Downloadable data exports

**Usage**: Manual after validation study completes

**Location**: `validation_results_<timestamp>/validation_report.html`

---

## 💡 Why Validation Matters

Before deploying VFScore to stakeholders (e.g., Archiproduct), validation provides:

1. **Reliability Evidence**: ICC ≥ 0.85 demonstrates consistent evaluations
2. **Stability Proof**: Low MAD shows predictable, reproducible scores
3. **Human Agreement**: High correlation validates automated scoring accuracy
4. **Configuration Optimization**: Identifies best temperature/top-p settings
5. **Transparency**: Complete provenance and methodology documentation

---

## ⚙️ Command-Line Options

```bash
python validation_study.py [OPTIONS]

Options:
  --run              Actually run the study (default: dry run only)
  --yes              Skip confirmation prompt
  --repeats N        Number of repeats per setting (default: 5)
  --model MODEL      LLM model to use (default: gemini-2.5-pro)
  -h, --help         Show help message
```

---

## 🛠️ Troubleshooting

### "vfscore: command not found"

**Solution**: Activate virtual environment:
```bash
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

### "selected_objects_optimized.csv not found"

**Solution**: The script uses mock data for demonstration. For production:
1. Ensure the CSV file exists in `validation_study/` directory
2. Or modify `objects_csv` path in the script

### Study runs but no results saved

**Solution**: Verify pipeline prerequisites:
```bash
vfscore ingest     # Ensure manifest exists
vfscore package    # Ensure scoring packets created
```

### Rate limit errors

**Solution**: The Gemini client handles rate limiting automatically. If errors persist:
- Set longer interval: `GEMINI_MIN_INTERVAL_SEC=60` in `.env`
- Use faster model: `--model gemini-2.5-flash`
- Reduce repeats: `--repeats 3`

---

## 🤝 Integration with VFScore

The validation framework is fully integrated with VFScore's core pipeline:

- Uses VFScore CLI commands (`vfscore score`, `vfscore aggregate`, etc.)
- Results stored in standard batch directories
- Compatible with multi-user batch system
- Metadata preserved across entire pipeline
- No modifications to production code required

---

## 📜 License

This validation framework is part of the VFScore project and follows the same MIT License.

---

## 👥 Contributing

Contributions welcome! See VFScore's main [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## 📞 Support

For questions or issues:
- Check the [Complete Guide](GUIDE.md)
- Review [Troubleshooting](#troubleshooting)
- Open an issue on GitHub

---

**Last Updated**: January 2025
**Status**: ✅ Production Ready
**VFScore Version**: Enhanced with Validation Study Support
