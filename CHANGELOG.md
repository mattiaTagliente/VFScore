# VFScore Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
