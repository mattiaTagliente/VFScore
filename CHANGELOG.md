# VFScore Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - CRITICAL: Cost Protection System (Headless Mode) 🛡️

**Date**: 2025-10-25

#### Comprehensive Billing Protection (Non-Interactive)

**CRITICAL UPDATE**: After a user received an unexpected €12.77 charge, we've implemented a comprehensive **headless** cost protection system to prevent accidental billing.

**Problem**: Google Gemini API automatically charges if billing is enabled on your Google Cloud project, with NO programmatic way to detect tier status before making calls.

**Solution**: Multi-layer protection system that prevents unexpected charges **WITHOUT any interactive prompts** (suitable for archi3D integration and automated workflows):

**1. Pre-Flight Billing Warning** (Non-Interactive):
- **Displayed before ANY API calls**
- Clear explanation of Free vs. Paid tiers
- Step-by-step instructions to check billing status
- **No prompts** - informational only
- Execution proceeds automatically

**2. Cost Estimation** (`CostEstimator`):
- Calculates token counts for images, messages, responses
- Estimates cost per call and total batch cost
- Based on current Gemini 2.5 Pro pricing:
  - Input: $1.25 per 1M tokens
  - Output: $10.00 per 1M tokens
- Shows both USD and EUR estimates

**3. Configuration-Based Cost Limit** (NEW):
- Set `scoring.max_cost_usd` in config
- **Automatic abort** if estimated cost exceeds limit
- No user prompt - execution stops immediately
- Example: `max_cost_usd: 5.0` (max $5 per run)

**4. Pre-Execution Check** (Non-Interactive):
- Shows detailed cost breakdown in table format:
  - Total API calls
  - Tokens per call
  - Cost per call
  - Total estimated cost (USD and EUR)
- Compares estimate against `max_cost_usd`
- **Auto-aborts if limit exceeded** - no user intervention required

**5. Real-Time Cost Tracking** (`CostTracker`):
- Records every API call with timestamp
- Tracks cumulative costs during execution
- Displays running cost after each item
- Saves detailed logs to `outputs/llm_calls/cost_tracker.json`

**6. Threshold Alerts** (Non-Interactive):
- Automatic alerts at: $1, $5, $10, $20 USD
- **Informational only** - no prompts
- Shows remaining budget if limit set
- **Auto-stops when max_cost_usd reached**
- Prevents runaway costs

**7. Final Cost Summary**:
- Displays complete cost breakdown at end
- Shows per-call and total costs
- Token counts and model info
- Warning message if costs were incurred
- Saves permanent log file

**New Files**:
- `src/vfscore/llm/cost_tracker.py` (500+ lines): Complete cost protection system

**Configuration Example**:
```yaml
# config.local.yaml
scoring:
  max_cost_usd: 5.0  # Maximum $5 per run (auto-abort if exceeded)
  display_billing_warning: true
  display_cost_estimate: true
```

**Example Output** (Headless - No Prompts):
```
Step 1: Billing Information
================================================================================
⚠  BILLING INFORMATION ⚠
================================================================================

The Gemini API has two modes:
  1. FREE TIER: No charges (5 RPM, 100 RPD limits)
  2. PAID TIER: Charges apply ($1.25/M input, $10/M output tokens)

CRITICAL: If you have billing enabled in Google Cloud,
you WILL be charged for API calls!

To check your billing status:
  1. Go to: https://aistudio.google.com/
  2. Check if billing is enabled for your project
  3. Disable billing to use FREE TIER only

VFScore cannot detect billing status programmatically.
Cost tracking and limits are enabled (see config).

Step 2: Cost Estimation
================================================================================
Cost Estimate for This Scoring Run
================================================================================

Model                   | Gemini 2.5 Pro
Items to Score          | 52
Repeats per Item        | 3
Total API Calls         | 156

Input Tokens per Call   | 5,000
Output Tokens per Call  | 800
Total Input Tokens      | 780,000
Total Output Tokens     | 124,800

Cost per Call           | $0.0137
TOTAL COST (USD)        | $2.14
TOTAL COST (EUR)        | €1.97

⚠ This will incur charges if billing is enabled!
Cost limit: $5.00 (from config)

[Execution proceeds automatically - no prompt]

Step 3: Starting Scoring
Scoring 52 items with gemini-2.5-pro (3 repeats each)...
Cost tracking enabled (logs: outputs/llm_calls/cost_tracker.json)

Scoring 558736 (1/52) ━━━━━━━━━━━━ 15% 0:25:00
  558736: 42.3s (3 repeats)
  Running cost: $0.0411

ℹ  COST THRESHOLD ALERT
Current cost: $1.02 USD (exceeded $1.00)
Remaining before limit: $3.98

[Continues automatically - no prompt]
```

**Protection Features** (Headless Mode):
- ✅ **No interactive prompts**: Completely automated execution
- ✅ **Config-based limits**: Set `max_cost_usd` to prevent overruns
- ✅ **Estimate before execute**: See costs before any API calls
- ✅ **Auto-abort**: Execution stops if cost limit exceeded
- ✅ **Continuous monitoring**: Running cost displayed after each item
- ✅ **Threshold alerts**: Informational alerts at $1, $5, $10, $20
- ✅ **Detailed logging**: Complete audit trail in JSON
- ✅ **Final summary**: Clear cost breakdown at end
- ✅ **archi3D compatible**: Safe for automated/scheduled workflows

**How to Avoid Charges**:
1. Go to https://aistudio.google.com/
2. Check "Billing" settings for your project
3. **Disable billing** to ensure FREE TIER only
4. Verify before running `vfscore score`

**Files Added**:
- `config.cost_protection.example.yaml`: Configuration example with detailed comments

**Files Modified**:
- `src/vfscore/scoring.py`: Integrated headless cost protection
- `src/vfscore/config.py`: Added cost protection config options

### Added - Async Multi-Key Scoring System 🚀

**Date**: 2025-10-25

#### Multi-Key Pool with Comprehensive Quota Tracking

VFScore now supports **team collaboration** with multiple API keys for dramatically faster scoring:

**New Features**:
- **`GeminiKeyPool`** (`src/vfscore/llm/key_pool.py`): Intelligent key rotation and quota management
  - **RPM Tracking**: 5 requests/minute per key (sliding window)
  - **TPM Tracking**: 125,000 tokens/minute per key (sliding window)
  - **RPD Tracking**: 100 requests/day per key (resets at midnight PT)
  - **Round-robin Selection**: Automatic load balancing across keys
  - **Quota-aware**: Skips exhausted keys, waits for available slots
  - **Warning Alerts**: 80% daily quota warnings per key
  - **Statistics Export**: JSON stats saved to `outputs/llm_calls/key_pool_stats.json`

- **`AsyncGeminiClient`** (`src/vfscore/llm/gemini_async.py`): Async LLM client with pool support
  - Concurrent scoring with `asyncio`
  - Intelligent rate limiting (respects all quotas)
  - Graceful error handling and retries
  - Backward compatible with single key mode

- **Configuration Support** (`src/vfscore/config.py`):
  - `scoring.api_keys`: List of API keys (supports `$ENV_VAR` references)
  - `scoring.key_labels`: Human-readable labels for logging (e.g., ["mattia", "colleague1"])
  - `scoring.use_async`: Enable/disable async mode (default: `true`)
  - `scoring.rpm_limit`, `tpm_limit`, `rpd_limit`: Per-key quotas

- **Updated `scoring.py`**:
  - `run_scoring_async()`: Async orchestration with progress tracking
  - `score_item_with_repeats_async()`: Concurrent repeat scoring
  - Automatic key pool creation and management
  - Real-time quota monitoring during execution
  - Maintains skip logic for resume capability

**Performance Improvements**:
- **Single key**: Async mode with better quota utilization (~2-3x faster)
- **Multiple keys**: Linear speedup with number of keys:
  - 2 keys: ~2x faster + 200 requests/day
  - 3 keys: ~3x faster + 300 requests/day
  - N keys: ~Nx faster + 100N requests/day

**Example Setup**:
```yaml
# config.local.yaml
scoring:
  use_async: true
  api_keys:
    - $GEMINI_API_KEY_USER1
    - $GEMINI_API_KEY_USER2
    - $GEMINI_API_KEY_USER3
  key_labels:
    - mattia
    - colleague1
    - colleague2
```

```bash
# .env
GEMINI_API_KEY_USER1=AIza...key1
GEMINI_API_KEY_USER2=AIza...key2
GEMINI_API_KEY_USER3=AIza...key3
```

**Compliance**: Fully compliant with Google ToS - designed for legitimate collaborative research teams.

**Backward Compatibility**: Single-key mode still works (uses `GEMINI_API_KEY` env var).

**Files Added**:
- `src/vfscore/llm/key_pool.py`: Key pool and quota tracking (400+ lines)
- `src/vfscore/llm/gemini_async.py`: Async Gemini client (250+ lines)
- `config.multikey.example.yaml`: Multi-key configuration example
- `validation_study/docs/API_PARALLELIZATION_PROPOSAL.md`: Complete technical documentation

**Usage**:
```bash
# Automatic (uses config.yaml settings)
vfscore score

# Will show:
# "Using async mode with intelligent rate limiting"
# "Initialized key pool with 3 keys: mattia, colleague1, colleague2"
# [Real-time quota stats during execution]
# [Final key pool statistics at end]
```

### Changed - Project Reorganization 📁

**Date**: 2025-10-24

#### Directory Structure Cleanup
- **Created `data/` directory**: All data files (CSV, JSON) now organized in dedicated folder
- **Created `scripts/` directory**: Utility scripts separated from root
- **Removed extra documentation**: Consolidated all docs into 3 main files (README, GUIDE, CHANGELOG)

#### Files Moved
- `database.csv` → `data/database.csv`
- `selected_objects_optimized.csv` → `data/selected_objects_optimized.csv`
- `selected_objects_for_study.csv` → `data/selected_objects_for_study.csv`
- `subjective.csv` → `data/subjective.csv`
- `VARIANT_ANALYSIS_SUMMARY.json` → `data/VARIANT_ANALYSIS_SUMMARY.json`
- `start_vfscore.bat` → `scripts/start_vfscore.bat`

#### Documentation Consolidation
- **Removed**: `CONFIGURATION_GUIDE.md`, `REORGANIZATION_SUMMARY.md`, `VALIDATION_STUDY_FIXES.md`
- **Kept**: Only 3 core documentation files (README.md, GUIDE.md, CHANGELOG.md) plus CLAUDE.md
- **Updated**: All configuration and usage information consolidated in GUIDE.md

#### Configuration Updates
- Updated `config.yaml`: Database paths now reference `data/` directory
- Updated `validation_study/validation_study.py`: CSV paths updated to `data/` prefix
- No breaking changes: All code references updated accordingly

**Why**: Clean root directory following modern project best practices, easier navigation, better organization

### Fixed - Item ID Validation and Windows Compatibility 🔧

#### Item ID Format Consistency
- **Fixed**: Item ID validation error for variants with spaces (e.g., "Curved backrest")
- Updated `src/vfscore/data_sources/base.py` to use `make_item_id()` for validation
- Ensures consistency: creation and validation use same sanitization logic
- Result: item_id "335888_curved-backrest" now validates correctly

#### Windows Terminal Compatibility
- **Fixed**: Unicode encoding errors on Windows terminals
- Replaced Unicode checkmarks (✓/✗) with ASCII equivalents ([OK]/[ERROR])
- Added `Console(legacy_windows=True)` for better Windows compatibility
- Updated `src/vfscore/__main__.py` across all commands

#### Pipeline Performance and Windows Encoding Improvements
**Date**: 2025-10-25

- **Added Skip Logic**: Pipeline now skips already-processed files to save time
  - `src/vfscore/render_cycles.py`: Checks if candidate.png exists before rendering
  - `src/vfscore/preprocess_gt.py`: Checks if gt_*.png exists before preprocessing
  - `src/vfscore/scoring.py`: Checks if all repeat files exist before re-scoring (resume capability)
  - Displays skip counts: "Skipped X already-rendered/processed/scored objects"
  - Result: Subsequent runs complete in seconds instead of hours
  - **Resume Capability**: Validation studies can be interrupted and resumed without losing progress

- **Fixed Windows Encoding in Progress Bars**:
  - Replaced `rich.progress.track()` with custom `Progress()` without emojis
  - Removed `SpinnerColumn` which uses Unicode spinner characters
  - Used only: `TextColumn`, `BarColumn`, `TaskProgressColumn`, `TimeRemainingColumn`
  - Sanitized Blender stdout/stderr to remove emojis: `encode('ascii', errors='ignore')`

- **Fixed Exception Message Encoding**:
  - Added `sanitize_error()` helper function in `__main__.py`
  - All exception messages sanitized before printing to console
  - Prevents crashes when exceptions contain emoji characters
  - Updated all 8 exception handlers in CLI commands

**Why**: Ensures pipeline performance optimization and complete Windows compatibility, eliminating all Unicode-related crashes

#### Enhanced Progress Tracking and Timing
**Date**: 2025-10-25

- **Elapsed Time Logging**: All pipeline steps now display elapsed time after completion
  - Added `format_elapsed_time()` helper for human-readable durations (e.g., "2m 30s", "1h 15m")
  - Added `timed_step()` context manager for automatic timing
  - All CLI commands wrapped with timing: ingest, preprocess-gt, render-cand, package, score, aggregate, translate, report
  - Displays: "Elapsed time: X.Xs" or "Xm Ys" or "Xh Ym" depending on duration

- **Detailed Scoring Progress**: Enhanced progress display in scoring module
  - Progress bar now shows current item being scored: "Scoring 558736 (3/52)"
  - Added `TimeRemainingColumn` for ETA estimation
  - Per-item timing: "335888: 125.3s (5 repeats)"
  - Total API calls and success rate displayed at end
  - Skip count displayed when resuming: "Skipped 45 already-scored items"

- **API Rate Limiting**: Verified correct configuration
  - Gemini 2.5 Pro: 31 seconds between calls (free tier: 2 req/min)
  - Configurable via `GEMINI_MIN_INTERVAL_SEC` environment variable
  - Proactive throttling prevents 429 errors

**Why**: Provides better user feedback during long-running operations, helps estimate completion time, and enables informed decisions about pausing/resuming validation studies

#### Validation Study Working Directory
- **Fixed**: Subprocess commands running from wrong directory
- All vfscore commands now use `cwd=str(vfscore_root)` parameter
- Ensures commands find config.local.yaml, database.csv, and other files
- Updated all subprocess calls in `validation_study/validation_study.py`

### Added - Database Abstraction Layer 🗄️

#### Core Data Source System
- **Database-Driven Architecture**: Complete refactoring from filesystem scanning to database-driven ingestion
- **Dual-Source Support**: Unified interface for both legacy (database.csv) and archi3D (tables/generations.csv) data sources
- **ItemRecord Data Model**: Comprehensive data model supporting (product_id, variant) as unique item identifier
- **Multiple Generations**: Each generation (algorithm + job_id) is now a separate manifest entry
- **Full Provenance**: Complete tracking of algorithm, job_id, variant, source_type in manifest

#### New Modules Created
- `src/vfscore/data_sources/base.py` - Core abstractions (ItemRecord dataclass, DataSource protocol)
- `src/vfscore/data_sources/legacy_source.py` - Legacy database.csv support with base_path resolution
- `src/vfscore/data_sources/archi3d_source.py` - Archi3D workspace integration
- `src/vfscore/data_sources/__init__.py` - Public exports

**ItemRecord Structure**:
```python
@dataclass
class ItemRecord:
    product_id: str          # e.g., "335888"
    variant: str             # e.g., "Curved backrest" or ""
    item_id: str             # Composite: "{product_id}_{variant}"
    ref_image_paths: List[Path]
    glb_path: Path
    algorithm: str           # e.g., "tripo3d_v2p5_multi"
    job_id: str              # Unique generation identifier
    # Metadata fields...
    source_type: str         # "legacy" or "archi3d"
```

#### Base Path Configuration
- **Single Base Path**: All legacy data paths resolved from one base directory
- **Relative GLB Paths**: GLB files resolved from `output_glb_relpath` in database.csv
- **Relative Dataset Folder**: Reference images folder relative to base_path
- **No Manual Copying**: Direct access to original file locations

**Configuration** (`config.yaml`):
```yaml
data_source:
  type: legacy  # "legacy" or "archi3d"

  # Legacy source (validation study)
  base_path: null  # Set in config.local.yaml
  dataset_folder: dataset  # Relative to base_path
  database_csv: database.csv
  selected_objects_csv: selected_objects_optimized.csv

  # Archi3D source (future integration)
  # workspace: path/to/Testing
  # run_id: "2025-08-17_v1"
```

### Changed - Ingest Module Refactoring

#### Complete Rewrite of Ingestion
- **Old Approach**: Filesystem scanning of `datasets/refs/` and `datasets/gens/`
- **New Approach**: Database-driven with configurable data sources
- **Path Resolution**: All paths now relative to base_path (legacy) or workspace (archi3D)
- **Enhanced Manifest**: Added product_id, variant, algorithm, job_id, source_type fields

**Before**: 7 manifest entries (limited by manual file copying)
**After**: 52 manifest entries (100% of selected items)

#### Breaking Changes
- `datasets/refs/` and `datasets/gens/` folders **no longer required**
- Configuration now requires `data_source.base_path` for legacy mode
- Manifest format includes new fields (backward compatible for reading)

#### New Configuration Model
- Added `DataSourceConfig` class in `src/vfscore/config.py`
- Path resolution updated to handle base_path
- Support for both legacy and archi3D configurations

**Enhanced Manifest Format**:
```json
{
  "item_id": "335888_Curved backrest",
  "product_id": "335888",
  "variant": "Curved backrest",
  "ref_paths": ["..."],
  "glb_path": "C:/.../Testing/runs/.../model.glb",
  "algorithm": "tripo3d_v2p5_multi",
  "job_id": "8a61ab220f6b8b147d0eb1ee30a8042207b12399",
  "n_refs": 3,
  "product_name": "LISA WOOD",
  "manufacturer": "S-CAB",
  "category_l1": "Arredo",
  "category_l2": "Tavoli e Sedie",
  "category_l3": "Sedie",
  "source_type": "legacy"
}
```

#### Data Model Improvements
- **Correct Item Identity**: Uses (product_id, variant) instead of just product_id
- **Multiple Generations**: Each (product_id, variant, algorithm, job_id) is a separate record
- **Complete Metadata**: Full category hierarchy, manufacturer, algorithm tracking
- **Source Tracking**: Records whether data came from legacy or archi3D source

**Why This Matters**:
- Enables proper handling of product variants (e.g., "Curved backrest" vs "Straight backrest")
- Supports multiple generations per item for comparative analysis
- Ready for archi3D integration (Phase 6 compatible)
- No more missing data due to incomplete file copying
- Single Source of Truth philosophy aligned with archi3D

### Added - Validation Study Framework ✅

#### Parameter Sweep Support
- **CLI Parameters**: Added `--temperature` and `--top-p` options to `vfscore score` command
- **Run ID Tracking**: Each evaluation gets unique `run_id` (UUID) for statistical independence
- **Metadata Logging**: All results include complete provenance (temperature, top_p, run_id, timestamp, model_name)
- **Configurable Sampling**: Override temperature and top_p from command line for validation studies

**Usage**:
```bash
# Custom temperature and top_p for validation study
vfscore score --model gemini-2.5-pro --repeats 5 --temperature 0.5 --top-p 0.95

# Use defaults from config
vfscore score --model gemini-2.5-pro --repeats 5
```

#### Enhanced Bilingual Validation Report
- **Full Bilingual Support**: Complete English/Italian validation reports
- **Interactive Help Menu**: Floating help button with comprehensive concept explanations
  - ICC (Intra-Class Correlation) - Reliability measurement
  - MAD (Median Absolute Deviation) - Stability measurement
  - Correlation (Pearson & Spearman) - Human agreement
  - MAE & RMSE - Error quantification
  - Temperature & Top-P - Sampling parameters explained
  - CI (Confidence Interval) - Uncertainty quantification
- **Language Toggle**: One-click switching between English and Italian
- **Persistent Preference**: Language choice saved in browser localStorage
- **Professional UI**: Modern gradient design with interactive charts (Chart.js, Plotly)

**Files Created**:
- `validation_report_generator_enhanced.py` - Enhanced bilingual report generator
- `validation_study.py` - Validation study orchestrator
- `PHASE1_IMPLEMENTATION_COMPLETE.md` - Implementation documentation
- `test_phase1.py` - Verification tests

#### Technical Changes
- `BaseLLMClient.__init__()`: Now accepts `run_id` parameter (auto-generates UUID if not provided)
- `GeminiClient.score_visual_fidelity()`: Adds `metadata` dict to all result JSONs
- `scoring.py`: Updated to generate unique run_id per repeat and pass parameters
- Prompts now include run_id nonce to prevent LLM caching and ensure independence

**Result JSON Format** (Enhanced):
```json
{
  "item_id": "558736",
  "score": 0.850,
  "subscores": {...},
  "rationale": [...],
  "metadata": {
    "temperature": 0.5,
    "top_p": 0.95,
    "run_id": "a7f3c4e2-9d1b-4a8f-b6e5-3c2f1a8d9e7b",
    "timestamp": "2025-10-23T14:23:45.123456",
    "model_name": "gemini-2.5-pro"
  }
}
```

**Why This Matters**:
- Enables systematic validation studies with parameter sweeps
- Ensures statistical independence across repeated evaluations
- Provides complete provenance tracking for all results
- Supports reliability analysis (ICC, MAD) and human agreement metrics
- Ready for Archiproduct presentation with bilingual reports

### Changed - Score Range Normalization

#### Breaking Change: Score Output Range
- **Scores now output in 0.000-1.000 range** (previously 0-100)
- LLM still scores internally on 0-100 scale for familiarity
- Automatic conversion to normalized range after scoring
- **Affected components**:
  - LLM client (`gemini.py`): Divides scores by 100 after parsing
  - Report display: Updated thresholds (0.8/0.6/0.4 instead of 80/60/40)
  - Subscore visualization: Updated to format as 0.000-1.000 with percentage bars
  - Summary statistics: Display format changed to 3 decimal places

**Migration Note**: If you have existing results in 0-100 range, they will continue to work but display differently. Re-run scoring for normalized output.

### Added - Bilingual Translation System 🌍

#### Translation Features
- **Automatic Translation**: LLM rationales now automatically translated from English to Italian
- **Translation Client**: New `TranslatorClient` using Gemini 2.5 Flash for fast, cost-effective translation
- **Translation Orchestration**: New `translate.py` module discovers and translates all scoring results
- **Smart Caching**: Translations cached as `rep_*_it.json` files to avoid re-translation
- **Batch Support**: Translations work seamlessly with batch system

#### CLI Commands
- `vfscore translate` - Translate existing results to Italian
- `vfscore translate --force` - Force re-translation of all results
- `vfscore translate --model gemini-2.5-flash` - Use specific translation model

#### Bilingual Reports
- **Interactive Language Switcher**: Toggle between English and Italian with one click
- **Side-by-side Content**: English and Italian rationales loaded simultaneously
- **Persistent Preference**: Language choice saved in browser localStorage
- **Fallback Handling**: Shows warning if translation missing, falls back to English
- **Responsive UI**: Beautiful bilingual UI with Bootstrap 5

#### Configuration
- New `translation` section in `config.yaml`
- `translation.enabled` - Enable/disable translation (default: true)
- `translation.model` - Model to use for translation (default: gemini-2.5-flash)
- `translation.cache_translations` - Cache translations to avoid re-translation (default: true)

#### Pipeline Integration
- `vfscore run-all` now includes translation step by default
- `vfscore run-all --skip-translation` to skip translation
- Translation runs after aggregation, before report generation

#### Documentation Consolidation
- **NEW: GUIDE.md** - Comprehensive guide consolidating installation, usage, configuration, development
- **Simplified README.md** - Concise overview with links to detailed guide
- **Updated CLAUDE.md** - Added translation workflow for Claude Code
- Removed obsolete documentation files to reduce fragmentation

### Changed

- Report generation now loads both English and Italian rationales
- HTML template updated with bilingual support and language switcher
- Pipeline now has 8 steps (was 7) with translation as step 6.5
- Documentation structure simplified from 13+ files to 3 core files

### Technical Details

- New modules: `src/vfscore/llm/translator.py`, `src/vfscore/translate.py`
- Translation uses JSON-based prompt/response for structured data
- Translation files (`rep_*_it.json`) contain metadata (timestamp, model used)
- Report JavaScript handles dynamic language switching without page reload
- Configuration validation added for translation settings via Pydantic

### Added - Phase 3: Pipeline Updates 🔄

#### Manifest-Driven Pipeline Architecture
- **Pipeline Refactoring**: All modules now read from `manifest.jsonl` instead of filesystem/database access
- **Database Abstraction**: Centralized data source logic with consistent ItemRecord model
- **Field Name Corrections**: Fixed field naming inconsistencies (`l1/l2/l3` → `category_l1/category_l2/category_l3`)

#### Updated Pipeline Modules
- **`ingest.py`**: Creates `manifest.jsonl` with complete metadata from data source
- **`preprocess_gt.py`**: Reads manifest to find reference images and process them
- **`render_cycles.py`**: Reads manifest to find GLB paths for rendering
- **`packetize.py`**: Reads manifest to create scoring packets (uses corrected field names)
- **`aggregate.py`**: Reads manifest to enrich results with category metadata
- **`report.py`**: Uses aggregated results that include enriched manifest data

#### Utility Enhancements
- **`utils.py`**: Added `make_item_id(product_id, variant)` utility function for consistent item ID generation
- **`archi3d_source.py`**: Updated to use `make_item_id()` for consistent naming
- **`legacy_source.py`**: Updated to use `make_item_id()` for consistent naming

#### Field Name Standardization
- **Manifest Structure**: All category fields now use `category_l1`, `category_l2`, `category_l3` format
- **Pipeline Consistency**: Fixed field access in packetize.py and aggregate.py to use correct names
- **Backward Compatibility**: Maintained compatibility while using standardized names

**Why This Matters**:
- Enables seamless integration with both legacy and archi3D data sources
- Provides consistent item ID generation across all data sources
- Eliminates field naming conflicts and improves maintainability
- Allows pipeline modules to work with unified manifest format
- Supports proper category hierarchy tracking throughout pipeline

## [0.1.0] - 2025-01-10

### Added - Phase 1 Complete ✅

#### Core Pipeline
- **Data Ingestion**: Automatic scanning of datasets and manifest creation
- **GT Preprocessing**: Background removal (rembg/U²-Net), standardization, cropping
- **Blender Rendering**: Automated Cycles rendering with fixed camera and HDRI lighting
- **Image Labeling**: Automatic label bars for GT and candidate images
- **LLM Scoring**: Gemini 2.0 Flash integration with structured JSON output
- **Score Aggregation**: Median computation with MAD-based confidence metrics
- **HTML Reporting**: Beautiful Bootstrap-based reports with embedded images

#### CLI Commands
- `vfscore ingest` - Scan and ingest dataset
- `vfscore preprocess-gt` - Process ground truth photos
- `vfscore render-cand` - Render candidate objects
- `vfscore package` - Create scoring packets
- `vfscore score` - Score with LLM (supports repeats)
- `vfscore aggregate` - Aggregate scores
- `vfscore report` - Generate HTML report
- `vfscore run-all` - Execute complete pipeline
- `vfscore --version` - Show version info

#### Configuration
- YAML-based configuration system
- Pydantic models for type safety
- Path resolution and validation
- Environment variable support (.env files)

#### Documentation
- Comprehensive README.md
- Detailed SETUP.md guide
- API documentation in docstrings
- Example .env file

#### Testing
- Setup verification script (`tests/test_setup.py`)
- Validates installation, paths, and API keys

#### Scoring Features
- 6-dimension rubric (color, materials, textures, artifacts)
- Configurable weights
- 3-repeat system for reliability
- JSON schema validation
- Automatic retry with exponential backoff

### Phase 2 - Planned

- [ ] Sentinel trials (positive/negative per l3 category)
- [ ] GPT-4V support for multi-model ensemble
- [ ] Advanced confidence metrics
- [ ] Enhanced HTML reports with comparison views
- [ ] Batch processing optimizations
- [ ] Logging and telemetry improvements

### Phase 3 - Future

- [ ] Web interface for report viewing
- [ ] Real-time progress dashboard
- [ ] Custom model training support
- [ ] Advanced analytics and visualizations
- [ ] Export to various formats (PDF, Excel)
- [ ] Integration with cloud storage

## Development Notes

### Technical Stack
- Python 3.11+
- Blender 4.5 (Cycles)
- Google Gemini 2.0 Flash
- rembg (U²-Net segmentation)
- Typer CLI
- Pydantic
- Rich (CLI formatting)
- Jinja2 (HTML templates)
- Bootstrap 5 (UI)

### Architecture Decisions
- Modern /src project structure
- Modular design with clear separation of concerns
- Configuration-driven approach
- Type hints throughout
- Error handling with retries
- Progress bars for user feedback
