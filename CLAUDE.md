# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VFScore is an automated pipeline for evaluating the **visual fidelity** of generated 3D objects (.glb files) against real product photographs using multimodal LLMs (primarily Google Gemini). It focuses exclusively on appearance (color, materials, textures) - geometry is assessed separately.

## Essential Commands

### Setup and Installation
```bash
# Interactive setup (recommended for first time)
python setup.py

# Manual setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .

# Create configuration files
cp .env.example .env      # Add your GEMINI_API_KEY
# Create config.local.yaml with your Blender path
```

### Development Commands
```bash
# Run complete pipeline
vfscore run-all
vfscore run-all --fast    # Faster rendering (128 samples vs 256)

# Run individual pipeline steps
vfscore ingest            # Scan datasets, create manifest
vfscore preprocess-gt     # Preprocess ground truth photos
vfscore render-cand       # Render 3D candidates with Blender
vfscore package           # Create scoring packets
vfscore score             # Score with LLM (default: gemini-2.5-pro)
vfscore aggregate         # Aggregate scores across batches
vfscore report            # Generate HTML report

# Scoring options
vfscore score --model gemini-2.5-flash --repeats 5
vfscore aggregate --latest-only          # Use only latest batch
vfscore aggregate --batch-pattern "user_mattia"  # Filter by user
vfscore aggregate --after 2025-10-01     # Filter by date
```

### Testing and Quality
```bash
pytest tests/                # Run all tests
python tests/test_setup.py   # Test setup verification

# Code formatting and linting
black src/                   # Format code (line-length: 100)
ruff check src/              # Lint code
mypy src/                    # Type checking
```

## Critical Architecture Concepts

### 1. Two-Layer Configuration System

The project uses a **two-layer configuration** to separate shared defaults from machine-specific settings:

- **`config.yaml`** (committed): Shared defaults for all developers
- **`config.local.yaml`** (not committed): Machine-specific overrides (Blender path, custom settings)

Implementation in `src/vfscore/config.py`:
- `Config.load()` reads `config.yaml` first
- Applies deep merge with `config.local.yaml` if it exists
- Uses Pydantic for validation
- All paths are resolved relative to project root

**Why this matters**: Never commit `config.local.yaml` or hardcode local paths in `config.yaml`. Always use `config.local.yaml` for machine-specific settings.

### 2. Batch System for Multi-User Collaboration (NEW)

**Critical**: The scoring system uses **self-describing batch directories** to accumulate results over time without overwriting:

```
outputs/llm_calls/<model>/<item_id>/
├── batch_20251011_143022_user_mattia/
│   ├── rep_1.json, rep_2.json, rep_3.json  # Scoring results
│   └── batch_info.json                      # Metadata (timestamp, user, config)
├── batch_20251011_150530_user_colleague/
│   └── ...
```

**Key files**:
- `src/vfscore/scoring.py`: Creates batch directories with `create_batch_directory_name()` and `create_batch_metadata()`
- `src/vfscore/aggregate.py`: Discovers all batches with `discover_batch_directories()` and merges them by default

**Configuration** (`config.yaml` or `config.local.yaml`):
```yaml
scoring:
  use_batch_mode: true       # Enable batch directories (default: true)
  results_dir: null          # null = local outputs/llm_calls
                             # or path to shared directory for collaboration
```

**Default behavior**: `vfscore aggregate` automatically discovers and aggregates **ALL batches** (not just latest) for better statistical assessment.

**Multi-user workflow**:
1. Each user runs `vfscore score` locally → creates timestamped batch
2. Copy `outputs/llm_calls/` folders to shared location
3. Run `vfscore aggregate` → automatically merges all batches
4. No merge conflicts (each batch is independent with embedded metadata)

### 3. Pipeline Architecture

The pipeline is a **7-step sequential process** orchestrated through CLI commands:

```
datasets/refs/*.jpg → ingest → preprocess-gt → [GT images]
datasets/gens/*.glb → ────────→ render-cand  → [Candidate images]
                                      ↓
                                  package (creates scoring packets)
                                      ↓
                                   score (LLM vision API)
                                      ↓
                                  aggregate (compute statistics)
                                      ↓
                                   report (HTML visualization)
```

**Key modules**:
- `ingest.py`: Scans datasets, creates `manifest.jsonl` with item metadata
- `preprocess_gt.py`: Background removal (rembg), canvas standardization, labeling
- `render_cycles.py`: Blender subprocess rendering with controlled camera/lighting
- `packetize.py`: Assembles GT + candidate images into scoring packets
- `scoring.py`: LLM API calls with retry logic and batch creation
- `aggregate.py`: Statistical aggregation (median, MAD, confidence)
- `report.py`: HTML report generation with thumbnails

**Data flow**: Each step reads from `outputs/` of previous step and writes to its own subdirectory. Pipeline state is implicit (file existence).

### 4. LLM Client Abstraction

**Base class**: `src/vfscore/llm/base.py:BaseLLMClient`
- Abstract interface for LLM vision clients
- Enforces consistent API: `score_visual_fidelity(image_paths, context, rubric_weights) -> Dict`
- Provides prompt templates (`_build_system_message()`, `_build_user_message()`)

**Current implementation**: `src/vfscore/llm/gemini.py:GeminiClient`
- Uses Google Generative AI SDK
- Implements rate limiting and retry logic
- Handles image encoding and API calls

**To add a new LLM**:
1. Create `src/vfscore/llm/newmodel.py` inheriting from `BaseLLMClient`
2. Implement `score_visual_fidelity()` and `_call_api()`
3. Update `scoring.py:get_llm_client()` to support new model
4. Add model to `config.yaml:scoring.models` list

### 5. Scoring Rubric

Visual fidelity is scored across **4 weighted dimensions**:

```python
# Default weights (configurable in config.yaml)
rubric_weights = {
    "color_palette": 40,           # 40%
    "material_finish": 25,          # 25%
    "texture_identity": 15,         # 15%
    "texture_scale_placement": 20,  # 20%
}
```

**Scoring flow**:
1. LLM receives GT images + candidate image
2. Scores each dimension [0-100]
3. Computes weighted sum: `final_score = Σ(weight_i × subscore_i)`
4. Returns JSON with subscores, final score, and rationale

**Important**: Geometry/silhouette is explicitly excluded. This is enforced in the prompt templates.

## File Organization Rules

### Never Commit
- `.env` - Contains API keys
- `config.local.yaml` - Machine-specific settings
- `outputs/` - Generated artifacts (too large)
- `venv/` - Virtual environment

### Always Commit
- `config.yaml` - Shared default configuration
- `src/` - Source code
- `tests/` - Test files
- Documentation (README.md, etc.)

### Virtual Environment
**Use `venv/` (not `.venv/`)** - The project standard is `venv/` for consistency.

## Common Development Patterns

### Adding a New Pipeline Step

1. Create module in `src/vfscore/newstep.py`:
```python
from vfscore.config import Config

def run_newstep(config: Config) -> None:
    """Run new pipeline step."""
    # Implementation
    pass
```

2. Add CLI command in `src/vfscore/__main__.py`:
```python
@app.command()
def newstep(config_path: Path = typer.Option("config.yaml")) -> None:
    """Description of new step."""
    from vfscore.newstep import run_newstep
    config = get_config()
    run_newstep(config)
```

3. Update `run_all()` to include new step in pipeline sequence

### Modifying Configuration

1. Update Pydantic model in `src/vfscore/config.py`
2. Update `config.yaml` with new default values
3. Document in README.md if user-facing

### Working with Batches

**Reading batch results**:
```python
from vfscore.aggregate import discover_batch_directories, filter_batch_directories

item_dir = Path("outputs/llm_calls/gemini/558736")
batch_dirs = discover_batch_directories(item_dir)
batch_dirs = filter_batch_directories(batch_dirs, latest_only=False)

# Load all results from all batches
for batch_dir in batch_dirs:
    for rep_file in batch_dir.glob("rep_*.json"):
        result = json.load(rep_file.open())
```

**Creating new batch**:
```python
# This is handled automatically by scoring.py when use_batch_mode=true
# Each run creates: batch_YYYYMMDD_HHMMSS_user_<username>/
```

## Important Implementation Details

### Blender Integration
- Uses **subprocess** to call Blender CLI (not bpy Python API)
- Blender path must be absolute in `config.local.yaml`
- Renders use Cycles engine with HDRI lighting (`assets/lights.hdr`)
- Camera parameters controlled via config: radius, azimuth, elevation

### Background Removal
- Uses `rembg` library with U2-Net model
- Model auto-downloads on first run (~180MB)
- Configurable model: `u2net` (default) or `u2net_human_seg` for people

### API Rate Limiting
- Gemini client implements exponential backoff
- Respects rate limits in `GeminiClient` class
- Retries failed API calls automatically

### Error Handling
- Pipeline steps are **fail-fast**: If a step fails, subsequent steps don't run
- Use Rich console for colored output and progress tracking
- Errors are logged but don't stop entire batch processing

## Dependencies

**Core**:
- `typer` - CLI framework
- `pydantic` - Config validation
- `google-generativeai` - Gemini API
- `pillow`, `opencv-python`, `numpy` - Image processing
- `rembg` - Background removal
- `rich` - Terminal UI

**External**:
- **Blender 4.2+** (separate installation, not a Python package)
- **Python 3.11+** required

## Testing Strategy

- Unit tests in `tests/` directory
- `test_setup.py` - Verifies environment setup
- Integration tests run pipeline steps on sample data
- Manual testing: `vfscore run-all --fast` on small dataset

## Performance Considerations

- **Rendering**: Slowest step (minutes per item). Use `--fast` (128 samples) for development
- **LLM API calls**: Rate-limited by provider. Batch multiple items when possible
- **Aggregation**: Fast, operates on JSON files only
- **Batch accumulation**: More batches = better statistics but slower aggregation (linear with batch count)

## Troubleshooting Common Issues

**"GEMINI_API_KEY not set"**
→ Ensure `.env` file exists in project root with valid key

**"Blender not found"**
→ Set absolute path in `config.local.yaml:paths.blender_exe`

**Import errors after git pull**
→ Run `pip install -e .` to reinstall package

**Aggregation finds no batches**
→ Check `config.yaml:scoring.use_batch_mode` is `true`
→ Verify batch directories exist in `outputs/llm_calls/<model>/<item_id>/`

**Legacy results compatibility**
→ Old results without batch structure are automatically treated as single "legacy" batch
