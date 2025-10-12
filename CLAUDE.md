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
vfscore run-all --fast              # Faster rendering (128 samples vs 256)
vfscore run-all --skip-translation  # Skip translation step

# Run individual pipeline steps
vfscore ingest            # Scan datasets, create manifest
vfscore preprocess-gt     # Preprocess ground truth photos
vfscore render-cand       # Render 3D candidates with Blender
vfscore package           # Create scoring packets
vfscore score             # Score with LLM (default: gemini-2.5-pro)
vfscore aggregate         # Aggregate scores across batches
vfscore translate         # Translate rationales to Italian
vfscore report            # Generate bilingual HTML report

# Scoring options
vfscore score --model gemini-2.5-flash --repeats 5
vfscore aggregate --latest-only          # Use only latest batch
vfscore aggregate --batch-pattern "user_mattia"  # Filter by user
vfscore aggregate --after 2025-10-01     # Filter by date

# Translation options
vfscore translate                        # Translate new results
vfscore translate --force                # Force re-translation
vfscore translate --model gemini-2.5-flash
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

### 1. Bilingual Translation System (NEW)

**Critical**: The scoring system now supports automatic English → Italian translation of LLM rationales:

#### Translation Architecture
- **Translation Client** (`src/vfscore/llm/translator.py`): Lightweight wrapper around Gemini 2.5 Flash
- **Translation Orchestration** (`src/vfscore/translate.py`): Discovers and translates scoring results
- **Caching Strategy**: Translations saved as `rep_*_it.json` alongside `rep_*.json`
- **Report Integration** (`src/vfscore/report.py`): Loads both languages, provides interactive switcher

#### Translation File Format
```
outputs/llm_calls/gemini-2.5-pro/558736/batch_XXX/
├── rep_1.json       # Original English
├── rep_1_it.json    # Italian translation
├── rep_2.json
├── rep_2_it.json
└── batch_info.json
```

**Translation JSON Structure**:
```json
{
  "item_id": "558736",
  "rationale_it": ["translated string 1", "translated string 2", ...],
  "translation_model": "gemini-2.5-flash",
  "translation_timestamp": "2025-01-12T14:30:00"
}
```

#### Configuration
```yaml
translation:
  enabled: true                # Enable Italian translation
  model: gemini-2.5-flash      # Fast and cost-effective
  cache_translations: true     # Cache to avoid re-translation
```

#### Key Functions
- `TranslatorClient.translate_rationale(rationale_en: List[str]) -> List[str]`: Translates list of strings
- `run_translation(config, model, force)`: Main translation orchestration
- `load_rationale_with_translation(llm_result_dir)`: Loads English + Italian rationales
- `discover_result_files(llm_calls_dir)`: Finds all `rep_*.json` files across batches
- `needs_translation(result_file)`: Checks if translation needed (caching logic)

#### Pipeline Integration
- **Automatic mode**: `vfscore run-all` includes translation after aggregation
- **Manual mode**: `vfscore translate` runs translation separately
- **Skip mode**: `vfscore run-all --skip-translation` skips translation step

#### Report Features
- **Language Switcher**: Top-right toggle in HTML report (English | Italiano)
- **Dynamic Content**: JavaScript switches visibility without page reload
- **Persistent Preference**: Language choice saved in browser localStorage
- **Fallback**: Shows English + warning if Italian translation missing

#### Why This Matters
- Translations are **cached** - run `vfscore translate` once, use forever
- **No overwriting** - translations are separate files (`rep_*_it.json`)
- **Batch-aware** - works seamlessly with multi-user batch system
- **Configurable** - can be enabled/disabled via config

### 2. Two-Layer Configuration System

The project uses a **two-layer configuration** to separate shared defaults from machine-specific settings:

- **`config.yaml`** (committed): Shared defaults for all developers
- **`config.local.yaml`** (not committed): Machine-specific overrides (Blender path, custom settings)

Implementation in `src/vfscore/config.py`:
- `Config.load()` reads `config.yaml` first
- Applies deep merge with `config.local.yaml` if it exists
- Uses Pydantic for validation
- All paths are resolved relative to project root

**Why this matters**: Never commit `config.local.yaml` or hardcode local paths in `config.yaml`. Always use `config.local.yaml` for machine-specific settings.

### 3. Batch System for Multi-User Collaboration

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

### 4. Pipeline Architecture

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

### 5. LLM Client Abstraction

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

### 6. Scoring Rubric

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

## Documentation Maintenance (CRITICAL)

**IMPORTANT**: After every significant change, you MUST update the documentation following this structure.

### Documentation Structure

VFScore uses a **3-file documentation system**:

1. **`README.md`** (Main entry point - ~300 lines)
   - Project overview and quick start
   - Features list and key capabilities
   - Quick usage examples
   - Links to detailed guides
   - **Update when**: Adding major features, changing quick start process, modifying installation

2. **`GUIDE.md`** (Comprehensive guide - ~900 lines)
   - Complete installation guide (interactive + manual)
   - Full pipeline documentation
   - Detailed configuration reference
   - Bilingual reports section
   - Development guide (code style, adding features)
   - Troubleshooting guide
   - Contributing guidelines
   - **Update when**: Adding CLI commands, modifying config structure, adding features, changing workflows

3. **`CHANGELOG.md`** (Version history)
   - Chronological record of all changes
   - Follows [Keep a Changelog](https://keepachangelog.com/) format
   - Sections: Added, Changed, Fixed, Deprecated, Removed
   - **Update when**: ANY change that affects users (always!)

### When to Update Documentation

**ALWAYS update documentation when you:**
- ✅ Add/modify CLI commands or options
- ✅ Add/change configuration options in `config.yaml`
- ✅ Add new modules or significant functionality
- ✅ Change file structure or output locations
- ✅ Modify workflows or usage patterns
- ✅ Fix bugs that affect user behavior
- ✅ Add or change dependencies
- ✅ Modify installation process

**Update order:**
1. **FIRST**: Update `CHANGELOG.md` (document what changed)
2. **THEN**: Update `GUIDE.md` (explain how to use it)
3. **FINALLY**: Update `README.md` if needed (quick start only)

### Documentation Update Checklist

After implementing changes, verify:

```markdown
## CHANGELOG.md Updates
- [ ] Added entry to [Unreleased] section
- [ ] Used correct category (Added/Changed/Fixed/etc.)
- [ ] Included clear description of user-facing changes
- [ ] Added technical details if relevant
- [ ] Mentioned new CLI commands/options

## GUIDE.md Updates
- [ ] Updated relevant sections (Installation/Usage/Configuration/etc.)
- [ ] Added examples for new features
- [ ] Updated command references
- [ ] Updated configuration examples
- [ ] Updated troubleshooting if needed
- [ ] Updated file structure diagrams if changed

## README.md Updates (if needed)
- [ ] Updated features list if major feature added
- [ ] Updated quick start if workflow changed
- [ ] Updated usage examples if commands changed
- [ ] Verified all links work
```

### Documentation Style Guide

**Commands and code:**
```markdown
# Use code blocks for commands
\`\`\`bash
vfscore translate --force
\`\`\`

# Inline code for files, commands, parameters
Run `vfscore translate` with `--force` option.
```

**Configuration examples:**
```markdown
# Always show full YAML context
\`\`\`yaml
translation:
  enabled: true
  model: gemini-2.5-flash
  cache_translations: true
\`\`\`
```

**File paths:**
```markdown
# Use relative paths from project root
outputs/llm_calls/<model>/<item_id>/rep_1_it.json
```

**Sections:**
- Use clear hierarchical headings (##, ###, ####)
- Start with overview, then details
- Include "Why this matters" for complex concepts

### Example: After Adding Translation Feature

**Step 1 - Update CHANGELOG.md:**
```markdown
## [Unreleased]

### Added - Bilingual Translation System
- `vfscore translate` command for translating results to Italian
- Interactive language switcher in HTML reports
- Automatic caching of translations
```

**Step 2 - Update GUIDE.md:**
- Add "Bilingual Reports" section with usage examples
- Update pipeline steps (now 8 instead of 7)
- Add configuration reference for `translation:` section
- Add troubleshooting entry for translation issues

**Step 3 - Update README.md:**
- Add "Bilingual Reports" to features list
- Add `vfscore translate` to usage examples
- Add translation section to quick overview

### Validation

Before considering documentation complete:

1. **Test commands**: Copy-paste commands from docs and verify they work
2. **Test config**: Verify config examples are valid YAML
3. **Test links**: Ensure all internal links work
4. **Read user perspective**: Would a new user understand this?

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
