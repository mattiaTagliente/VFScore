# VFScore Complete Guide

**Version**: 0.1.0
**Last Updated**: January 2025

A comprehensive guide covering installation, usage, configuration, bilingual reporting, development, and contribution guidelines for VFScore.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Bilingual Reports (English/Italian)](#bilingual-reports-englishitalian)
- [Configuration](#configuration)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Installation

### Prerequisites

- **Python 3.11+** installed
- **Blender 4.2+** for rendering ([Download](https://www.blender.org/download/))
- **Git** for version control
- **API Keys**:
  - Google Gemini API key (required) - Get from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Option 1: Interactive Setup (Recommended)

The easiest way to get started:

```bash
# Clone repository
git clone https://github.com/mattiaTagliente/VFScore.git
cd VFScore

# Run interactive setup
python setup.py
```

The setup script will:
- Create your `.env` file with API keys
- Create `config.local.yaml` with machine-specific settings
- Auto-detect your Blender installation
- Install Python dependencies
- Verify the setup

### Option 2: Manual Setup

If you prefer manual configuration:

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -e .

# 4. Create .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 5. Create config.local.yaml
# Create a file named config.local.yaml in project root:
```

**config.local.yaml** (Machine-specific settings):
```yaml
paths:
  blender_exe: "YOUR_BLENDER_PATH"
  # Windows example: "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
  # macOS example: "/Applications/Blender.app/Contents/MacOS/Blender"
  # Linux example: "/usr/bin/blender"

# Optional: customize settings
render:
  samples: 128  # Lower for faster testing (default: 256)

translation:
  enabled: true  # Enable Italian translation
```

### Verification

Test your installation:

```bash
# Check CLI is working
vfscore --version

# Run setup verification
python tests/test_setup.py
```

---

## Quick Start

### Complete Pipeline

Run everything at once:

```bash
vfscore run-all
```

This executes all 8 steps:
1. **Ingest**: Scan dataset and create manifest
2. **Preprocess GT**: Remove backgrounds from reference photos
3. **Render**: Render 3D candidates with Blender
4. **Package**: Create scoring packets with labels
5. **Score**: Evaluate with LLM (Gemini 2.5 Pro)
6. **Aggregate**: Compute statistics and confidence
7. **Translate**: Generate Italian translations
8. **Report**: Create bilingual HTML report

### Individual Steps

Run steps separately for debugging or partial updates:

```bash
vfscore ingest              # Scan datasets
vfscore preprocess-gt       # Preprocess ground truth
vfscore render-cand         # Render candidates
vfscore package             # Create scoring packets
vfscore score               # Score with LLM
vfscore aggregate           # Aggregate scores
vfscore translate           # Translate to Italian
vfscore report              # Generate HTML report
```

### Common Options

```bash
# Fast rendering (128 samples instead of 256)
vfscore run-all --fast

# Use different scoring model
vfscore score --model gemini-2.5-flash

# More repeats for higher confidence
vfscore score --repeats 5

# Skip translation step
vfscore run-all --skip-translation

# Force re-translation
vfscore translate --force

# View help for any command
vfscore --help
vfscore score --help
```

### Daily Workflow

```bash
# 1. Activate virtual environment
.\venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux

# 2. Add new items to datasets/refs/ and datasets/gens/

# 3. Run pipeline
vfscore run-all

# 4. View report
# Open outputs/report/index.html in your browser
```

---

## Usage

### Dataset Structure

Organize your data as follows:

```
VFScore/
├── datasets/
│   ├── refs/           # Reference photos (ground truth)
│   │   ├── 558736/
│   │   │   ├── photo1.jpg
│   │   │   └── photo2.jpg
│   │   └── 709360/
│   │       └── photo1.png
│   └── gens/           # Generated 3D objects
│       ├── 558736/
│       │   └── model.glb
│       └── 709360/
│           └── model.glb
└── metadata/
    └── categories.csv  # Item categories (l1, l2, l3)
```

**categories.csv** format:
```csv
item_id,l1,l2,l3
558736,Furniture,Tables and Chairs,Chairs
709360,Furniture,Tables and Chairs,Tables
```

### Understanding the Pipeline

#### 1. Ingest (`vfscore ingest`)
- Scans `datasets/refs/` and `datasets/gens/`
- Loads category metadata from `metadata/categories.csv`
- Creates `outputs/manifest.jsonl` with all items

#### 2. Preprocess GT (`vfscore preprocess-gt`)
- Removes backgrounds using U²-Net segmentation
- Crops to content with margin
- Standardizes to 1024×1024 PNG
- Outputs to `outputs/preprocess/refs/<item_id>/`

#### 3. Render Candidates (`vfscore render-cand`)
- Renders .glb files using Blender Cycles
- Fixed three-quarter camera view
- Studio HDRI lighting (`assets/lights.hdr`)
- Outputs to `outputs/preprocess/cand/<item_id>/`

#### 4. Package (`vfscore package`)
- Adds label bars to images (GT #1, GT #2, CANDIDATE)
- Creates scoring packets combining all views
- Outputs to `outputs/labels/<item_id>/`

#### 5. Score (`vfscore score`)
- Sends images to LLM (default: Gemini 2.5 Pro)
- Evaluates visual fidelity across 4 dimensions
- Runs multiple repeats (default: 3) for reliability
- Each repeat gets unique `run_id` for statistical independence
- Supports custom `temperature` and `top_p` parameters for validation studies
- Outputs to `outputs/llm_calls/<model>/<item_id>/batch_*/`

**Advanced Scoring Options**:
```bash
# Validation study with custom sampling parameters
vfscore score --repeats 5 --temperature 0.5 --top-p 0.95

# More deterministic scoring
vfscore score --temperature 0.0 --top-p 1.0

# Use config defaults
vfscore score
```

#### 6. Aggregate (`vfscore aggregate`)
- Computes median scores across repeats
- Calculates confidence metrics (MAD-based)
- Merges results across all batches
- Outputs to `outputs/results/per_item.jsonl` and `.csv`

#### 7. Translate (`vfscore translate`)
- Translates LLM rationales from English to Italian
- Uses Gemini 2.5 Flash for speed and cost-efficiency
- Caches translations to avoid re-translation
- Outputs to `outputs/llm_calls/<model>/<item_id>/batch_*/rep_*_it.json`

#### 8. Report (`vfscore report`)
- Generates bilingual HTML report
- Embeds images and scores
- Interactive language switcher
- Outputs to `outputs/report/index.html`

### Scoring Rubric

Visual fidelity is evaluated across 4 weighted dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Color & Palette** | 40% | Overall hue, saturation, brightness |
| **Material Finish** | 25% | Metallic/dielectric, roughness, specular |
| **Texture Identity** | 15% | Correct patterns, logos, prints |
| **Texture Scale & Placement** | 20% | Scale, alignment, seams |

**Final Score** = Weighted sum [0.000-1.000]

**Note**: Geometry/silhouette is explicitly **excluded** - VFScore evaluates appearance only.

### Batch System

VFScore uses **timestamped batch directories** to accumulate results without overwriting:

```
outputs/llm_calls/gemini-2.5-pro/558736/
├── batch_20251011_143022_user_mattia/
│   ├── rep_1.json, rep_2.json, rep_3.json      # Scores
│   ├── rep_1_it.json, rep_2_it.json, rep_3_it.json  # Translations
│   └── batch_info.json                         # Metadata
├── batch_20251012_091530_user_colleague/
│   └── ...
```

**Benefits:**
- Multiple users can score independently
- Results accumulate over time
- No overwriting or merge conflicts
- Better statistical assessment with more data

**Aggregation:** By default, `vfscore aggregate` merges **ALL batches**. Use `--latest-only` to use only the most recent batch.

### Output Files

```
outputs/
├── manifest.jsonl                     # Item inventory
├── preprocess/
│   ├── refs/<item_id>/gt_*.png       # Processed GT images
│   └── cand/<item_id>/candidate.png  # Rendered candidates
├── labels/<item_id>/                 # Labeled images
│   ├── gt_*_labeled.png
│   ├── candidate_labeled.png
│   └── packet.json
├── llm_calls/<model>/<item_id>/
│   └── batch_*/                      # Scoring results by batch
│       ├── rep_*.json                # English scores
│       ├── rep_*_it.json             # Italian translations
│       └── batch_info.json           # Batch metadata
├── results/
│   ├── per_item.csv                  # Summary scores
│   └── per_item.jsonl                # Detailed records
└── report/
    └── index.html                    # Bilingual HTML report
```

---

## Bilingual Reports (English/Italian)

### Overview

VFScore generates bilingual reports with interactive language switching. LLM rationales are automatically translated to Italian using Gemini 2.5 Flash.

### Features

- **Interactive Language Toggle**: Switch between English and Italian with one click
- **Automatic Translation**: LLM rationales translated using Gemini 2.5 Flash
- **Smart Caching**: Translations cached to avoid redundant API calls
- **Fallback Handling**: Shows English if translation missing
- **Persistent Preference**: Language choice saved in browser

### Usage

#### Enable/Disable Translation

In `config.yaml` or `config.local.yaml`:

```yaml
translation:
  enabled: true                # Enable Italian translation
  model: gemini-2.5-flash      # Translation model
  cache_translations: true     # Cache translations
```

#### Translation Workflow

**Option 1: Automatic (Recommended)**

```bash
# Run complete pipeline with translation
vfscore run-all
```

Translation happens automatically after scoring.

**Option 2: Manual**

```bash
# Score items first
vfscore score

# Translate separately
vfscore translate

# Generate report
vfscore report
```

**Option 3: Skip Translation**

```bash
# Skip translation in run-all
vfscore run-all --skip-translation
```

#### Force Re-translation

To re-translate existing results:

```bash
vfscore translate --force
```

This is useful when:
- Improving translation quality
- Updating to a new translation model
- Fixing translation errors

### How It Works

1. **Scoring**: LLM generates rationales in English
   - Files: `rep_1.json`, `rep_2.json`, etc.

2. **Translation**: Gemini 2.5 Flash translates rationales
   - Files: `rep_1_it.json`, `rep_2_it.json`, etc.
   - Contains: `rationale_it`, `translation_model`, `translation_timestamp`

3. **Report Generation**: HTML report loads both languages
   - English version visible by default
   - Italian version hidden until user switches
   - JavaScript toggles visibility on language switch

### Translation File Format

**rep_1_it.json** example:
```json
{
  "item_id": "558736",
  "rationale_it": [
    "La palette di colori è completamente errata...",
    "Le finiture dei materiali sono sbagliate..."
  ],
  "translation_model": "gemini-2.5-flash",
  "translation_timestamp": "2025-01-12T14:30:00"
}
```

### Viewing Reports

Open `outputs/report/index.html` in your browser. Use the language toggle in the header:

- **English** button: Show English rationales
- **Italiano** button: Show Italian rationales

Your preference is saved automatically.

---

## Validation Studies

### Overview

VFScore includes a comprehensive framework for validation studies to assess:
- **Reliability**: Consistency of evaluations (ICC, MAD)
- **Stability**: Score dispersion across repeated measurements
- **Human Agreement**: Correlation with human evaluators

### Parameter Sweep Support

The system supports systematic parameter sweeps for validation studies:

```bash
# Example: Test different temperature settings
vfscore score --repeats 5 --temperature 0.0 --top-p 1.0  # Baseline
vfscore score --repeats 5 --temperature 0.2 --top-p 1.0  # Test 1
vfscore score --repeats 5 --temperature 0.5 --top-p 0.95 # Test 2
vfscore score --repeats 5 --temperature 0.8 --top-p 0.9  # Test 3
```

### Key Features

#### Run ID Tracking
- Each evaluation gets a unique `run_id` (UUID)
- Run ID included in prompt to prevent LLM caching
- Ensures statistical independence across repeated evaluations

#### Complete Metadata
All result JSON files include:
```json
{
  "item_id": "558736",
  "score": 0.850,
  "metadata": {
    "temperature": 0.5,
    "top_p": 0.95,
    "run_id": "unique-uuid",
    "timestamp": "2025-10-23T14:23:45",
    "model_name": "gemini-2.5-pro"
  }
}
```

### Validation Study Workflow

1. **Select Test Objects**: Choose diverse items across categories
2. **Run Parameter Sweep**: Test different temperature/top_p combinations
3. **Collect Results**: All batches automatically accumulated
4. **Analyze Metrics**: Compute ICC, MAD, correlations
5. **Generate Report**: Create bilingual validation report with help menu

### Enhanced Validation Reports

The validation study framework includes enhanced bilingual reports with:

- **Interactive Help Menu**: Floating `?` button with concept explanations
  - ICC (Intra-Class Correlation)
  - MAD (Median Absolute Deviation)
  - Correlation (Pearson & Spearman)
  - MAE & RMSE
  - Temperature & Top-P parameters
  - Confidence Intervals
- **Language Toggle**: English/Italian switching
- **Interactive Charts**: Chart.js and Plotly visualizations
- **Download Options**: Export JSON and CSV data

### Example Validation Study

See `PHASE1_IMPLEMENTATION_COMPLETE.md` for complete implementation details and `validation_study.py` for the orchestration framework.

---

## Configuration

### Two-Layer System

VFScore uses a two-layer configuration to separate shared defaults from machine-specific settings:

1. **`config.yaml`** (Shared defaults - committed to git)
2. **`config.local.yaml`** (Personal overrides - NOT committed)

**How it works:**
- VFScore loads `config.yaml` first
- If `config.local.yaml` exists, its values override defaults
- This allows personalization without modifying shared settings

### Configuration Sections

#### Paths

```yaml
paths:
  refs_dir: datasets/refs
  gens_dir: datasets/gens
  categories: metadata/categories.csv
  hdri: assets/lights.hdr
  out_dir: outputs
  blender_exe: "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
```

#### Rendering

```yaml
render:
  engine: cycles
  samples: 256           # Lower for faster rendering (e.g., 128)
  fov_deg: 42
  camera:
    radius: 2.2
    azimuth_deg: 45
    elevation_deg: 35
  resolution: 1024
  denoiser: OIDN
```

#### Preprocessing

```yaml
preprocess:
  canvas_px: 1024
  bg_rgb: [0, 0, 0]
  segmentation_model: "u2net"  # or "u2net_human_seg" for people
```

#### Scoring

```yaml
scoring:
  models: [gemini-2.5-pro]
  repeats: 3
  rubric_weights:
    color_palette: 40
    material_finish: 25
    texture_identity: 15
    texture_scale_placement: 20
  temperature: 0.0           # Default sampling temperature (0.0 = deterministic)
  top_p: 1.0                 # Default top-p sampling (1.0 = all tokens)
  use_batch_mode: true       # Enable timestamped batches
  results_dir: null          # null = local, or path to shared directory
```

**Note**: `temperature` and `top_p` can be overridden from CLI:
```bash
vfscore score --temperature 0.5 --top-p 0.95
```

This enables **validation studies** to sweep across different parameter settings while maintaining independent evaluations (each repeat gets unique `run_id`).

#### Translation

```yaml
translation:
  enabled: true                    # Enable Italian translation
  model: gemini-2.5-flash          # Fast and cost-effective
  cache_translations: true         # Cache to avoid re-translation
```

### Environment Variables

Create `.env` file in project root:

```bash
# Required
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Optional: Override minimum interval between API calls (seconds)
GEMINI_MIN_INTERVAL_SEC=31
```

**Important:** Never commit `.env` to git!

---

## Development

### Setting Up for Development

```bash
# Clone repository
git clone https://github.com/mattiaTagliente/VFScore.git
cd VFScore

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install in editable mode
pip install -e .

# Install development dependencies
pip install pytest black ruff mypy

# Test installation
vfscore --version
python tests/test_setup.py
```

### Project Structure

```
VFScore/
├── src/vfscore/              # Main package
│   ├── __main__.py          # CLI entry point (Typer)
│   ├── config.py            # Configuration management
│   ├── ingest.py            # Data ingestion
│   ├── preprocess_gt.py     # GT preprocessing
│   ├── render_cycles.py     # Blender rendering
│   ├── packetize.py         # Scoring packets
│   ├── scoring.py           # LLM scoring orchestration
│   ├── translate.py         # Translation orchestration
│   ├── aggregate.py         # Score aggregation
│   ├── report.py            # Bilingual report generation
│   ├── utils.py             # Utilities
│   └── llm/                 # LLM client implementations
│       ├── base.py          # Abstract client
│       ├── gemini.py        # Gemini implementation
│       └── translator.py    # Translation client
├── tests/                    # Test files
│   └── test_setup.py        # Setup verification
├── datasets/                 # Data (not in git)
├── metadata/                 # Category metadata
├── assets/                   # HDRI lighting
├── outputs/                  # Generated outputs (not in git)
├── config.yaml               # Shared config (commit)
├── config.local.yaml         # Local config (DO NOT commit)
├── .env                      # API keys (DO NOT commit)
└── README.md                 # Project overview
```

### Code Style

We follow **PEP 8** with modifications:

- **Line length**: 100 characters
- **Quotes**: Double quotes for strings
- **Type hints**: Always use type hints
- **Docstrings**: Google-style docstrings

**Formatting Tools:**

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

### Adding New Features

#### Adding a New LLM Model

1. Create client in `src/vfscore/llm/`:
   ```python
   # src/vfscore/llm/gpt4v.py
   from vfscore.llm.base import BaseLLMClient

   class GPT4VClient(BaseLLMClient):
       def score_visual_fidelity(self, image_paths, context, rubric_weights):
           # Implementation
           pass
   ```

2. Update `scoring.py:get_llm_client()` to support new model

3. Add model to `config.yaml:scoring.models`

4. Update documentation

#### Adding a New CLI Command

1. Add command in `src/vfscore/__main__.py`:
   ```python
   @app.command()
   def my_command(
       param: str = typer.Option("default", help="Help text"),
       config_path: Path = typer.Option("config.yaml"),
   ) -> None:
       """Command description."""
       from vfscore.my_module import run_my_function

       config = get_config()
       run_my_function(config, param)
   ```

2. Create corresponding module in `src/vfscore/`

3. Update documentation

#### Modifying Configuration

1. Update Pydantic model in `src/vfscore/config.py`
2. Update `config.yaml` with new defaults
3. Document in this guide

### Testing

```bash
# Run all tests
pytest tests/

# Run specific test
python tests/test_setup.py

# Run with coverage
pytest --cov=vfscore tests/
```

### Git Workflow

1. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test:**
   ```bash
   # Make your changes
   # Test thoroughly
   vfscore run-all --fast
   ```

3. **Commit with clear message:**
   ```bash
   git add <files>
   git commit -m "feat: add new feature"
   ```

   **Commit prefixes:**
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation
   - `refactor:` - Code refactoring
   - `test:` - Tests
   - `chore:` - Maintenance

4. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

---

## Troubleshooting

### Installation Issues

**Problem**: `GEMINI_API_KEY not set`
**Solution**: Ensure `.env` file exists with your API key. Run `python setup.py` to create it interactively.

**Problem**: `Blender not found`
**Solution**: Update `blender_exe` path in `config.local.yaml`. Run `python setup.py` to auto-detect Blender.

**Problem**: `Import error: vfscore`
**Solution**: Ensure virtual environment is activated and run `pip install -e .` from project root.

**Problem**: `rembg` model download fails
**Solution**: Check internet connection. Model (~180MB) downloads on first run. Try manually: `python -c "from rembg import new_session; new_session('u2net')"`

### Runtime Issues

**Problem**: Rendering fails with GPU error
**Solution**: Update GPU drivers. Or disable GPU in `config.local.yaml`:
```yaml
render:
  use_gpu: false
```

**Problem**: API rate limit errors (429)
**Solution**: The Gemini client automatically handles rate limiting with exponential backoff. If errors persist, set a longer interval:
```bash
# In .env
GEMINI_MIN_INTERVAL_SEC=60
```

**Problem**: Translation not showing in report
**Solution**:
1. Verify `translation.enabled: true` in config
2. Run `vfscore translate` manually
3. Check for `rep_*_it.json` files in batch directories
4. Regenerate report: `vfscore report`

**Problem**: Aggregation finds no batches
**Solution**:
1. Check `config.yaml:scoring.use_batch_mode` is `true`
2. Verify batch directories exist in `outputs/llm_calls/<model>/<item_id>/`
3. Run `vfscore score` to create results first

### Configuration Issues

**Problem**: Changes in `config.yaml` not taking effect
**Solution**: Check if `config.local.yaml` overrides them. Local config takes precedence.

**Problem**: Accidentally committed `.env` or `config.local.yaml`
**Solution**:
```bash
git rm --cached .env config.local.yaml
git commit -m "Remove sensitive files from git"
# Update .gitignore to ensure they stay ignored
```

### Performance Issues

**Problem**: Rendering too slow
**Solution**:
1. Use `--fast` mode: `vfscore run-all --fast`
2. Lower samples in config:
   ```yaml
   render:
     samples: 128  # or even 64 for testing
   ```

**Problem**: Translation taking too long
**Solution**: Translation uses Gemini 2.5 Flash which is fast. If slow:
1. Check API rate limits
2. Verify internet connection
3. Use `--force` sparingly (only when needed)

---

## Contributing

### Before Contributing

1. Read this guide thoroughly
2. Check [existing issues](https://github.com/mattiaTagliente/VFScore/issues)
3. Discuss major changes in an issue first

### Contribution Process

1. **Fork the repository**

2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/VFScore.git
   cd VFScore
   ```

3. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature
   ```

4. **Make changes:**
   - Write clear, documented code
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation

5. **Test your changes:**
   ```bash
   python tests/test_setup.py
   vfscore run-all --fast
   pytest tests/
   ```

6. **Format and lint:**
   ```bash
   black src/
   ruff check src/
   ```

7. **Commit:**
   ```bash
   git add <files>
   git commit -m "feat: descriptive message"
   ```

8. **Push and create PR:**
   ```bash
   git push origin feature/your-feature
   ```
   Then create Pull Request on GitHub.

### Pull Request Guidelines

**PR Description should include:**
- Clear description of changes
- Motivation for the changes
- Type of change (bug fix, feature, docs, etc.)
- Testing performed
- Screenshots (if UI changes)

**Checklist:**
- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No sensitive data committed
- [ ] Commit messages are clear
- [ ] No breaking changes (or documented)

### Code of Conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on the code, not the person
- Provide helpful feedback

### Getting Help

- 📖 Read this guide and README.md
- 🐛 Check [GitHub Issues](https://github.com/mattiaTagliente/VFScore/issues)
- 💬 Create new issue with:
  - Clear description
  - Steps to reproduce
  - System information
  - Error messages/logs

---

## Additional Resources

### Documentation
- [README.md](README.md) - Project overview and quick start
- [CHANGELOG.md](CHANGELOG.md) - Version history and breaking changes
- [CLAUDE.md](CLAUDE.md) - Claude Code project instructions

### External Links
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Blender Python API](https://docs.blender.org/api/current/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

### Performance Metrics

**Per Item** (typical):
- Ingestion: < 1 second
- GT Preprocessing: 5-10 seconds
- Rendering: 5-7 minutes (GPU)
- Scoring: 3-5 seconds per repeat
- Translation: 2-3 seconds per item
- **Total**: ~10-15 minutes per item

**Resource Usage**:
- GPU: Required for fast rendering
- RAM: ~2-4 GB peak
- Disk: ~5-10 MB per item

### API Costs

**Gemini 2.5 Pro** (Scoring):
- Free tier: 2 requests/minute
- Paid tier: Higher rate limits
- Cost per item: 3 API calls (3 repeats)

**Gemini 2.5 Flash** (Translation):
- Free tier: Higher rate limits than Pro
- Very cost-effective for translation
- Cost per item: 1-3 API calls (depends on number of result files)

---

## License

MIT License - see LICENSE file for details.

---

## Contact & Support

- **GitHub**: [github.com/mattiaTagliente/VFScore](https://github.com/mattiaTagliente/VFScore)
- **Issues**: [github.com/mattiaTagliente/VFScore/issues](https://github.com/mattiaTagliente/VFScore/issues)

---

**Thank you for using VFScore!** 🎉
