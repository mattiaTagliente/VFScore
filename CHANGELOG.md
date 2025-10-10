# VFScore Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
