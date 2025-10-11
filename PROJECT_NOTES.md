# VFScore - Project Notes

## Project Overview
VFScore is an automated pipeline for evaluating the visual fidelity of generated 3D objects against real product photographs using multimodal LLMs (primarily Google Gemini).

**Key Focus**: Evaluates appearance only (color, materials, textures) - geometry quality is assessed separately using F-SCORE.

## Project Structure

```
VFScore/
├── src/vfscore/          # Source code
│   ├── __main__.py       # CLI entry point (typer-based)
│   ├── config.py         # Configuration management (Pydantic)
│   ├── ingest.py         # Data ingestion
│   ├── preprocess_gt.py  # GT photo preprocessing
│   ├── render_cycles.py  # Blender Cycles rendering
│   ├── packetize.py      # Scoring packet assembly
│   ├── scoring.py        # LLM scoring orchestration
│   ├── aggregate.py      # Score aggregation
│   ├── report.py         # Report generation
│   └── llm/              # LLM client implementations
│       └── gemini.py     # Google Gemini client
├── datasets/
│   ├── refs/             # Reference photos (GT)
│   └── gens/             # Generated .glb files
├── metadata/
│   └── categories.csv    # Item categories (l1, l2, l3)
├── outputs/              # Generated artifacts (not in git)
│   ├── preprocess/       # Preprocessed images
│   ├── labels/           # Labeled images + packets
│   ├── llm_calls/        # Raw LLM responses (BATCH STRUCTURE)
│   ├── results/          # Aggregated results
│   └── report/           # HTML reports
├── venv/                 # Virtual environment (NOT .venv)
├── config.yaml           # Shared default config
├── config.local.yaml     # Machine-specific overrides (not in git)
└── .env                  # API keys (not in git)
```

## Configuration System

Two-layer configuration approach:
- `config.yaml` - Shared defaults (committed)
- `config.local.yaml` - Machine-specific overrides (not committed)

Key config sections:
- `paths`: File locations, Blender path
- `render`: Blender rendering settings (samples, resolution, camera)
- `preprocess`: Image preprocessing settings
- `scoring`: LLM settings, rubric weights, **batch mode**, results directory
- `sentinels`: Sentinel trials (Phase 2 feature)
- `logging`: Logging configuration

## Pipeline Steps (CLI Commands)

```bash
vfscore run-all              # Complete pipeline
vfscore ingest               # 1. Scan dataset, create manifest
vfscore preprocess-gt        # 2. Preprocess GT photos
vfscore render-cand          # 3. Render candidates with Blender
vfscore package              # 4. Create scoring packets
vfscore score                # 5. Score with LLM
vfscore aggregate            # 6. Aggregate scores
vfscore report               # 7. Generate HTML report
```

## Scoring Rubric

4 dimensions with weighted scoring:
- Color & Palette: 40%
- Material Finish: 25%
- Texture Identity: 15%
- Texture Scale & Placement: 20%

**Final Score**: Weighted sum [0-100]

## Batch System (NEW - Implemented 2025-10-11)

### Key Features
- **Self-describing batches**: Each batch is independent with embedded metadata
- **No overwrites**: Each scoring run creates a new timestamped batch
- **Multi-user support**: Simple file copying for collaboration
- **Automatic aggregation**: Discovers and merges all batches by default

### Batch Directory Structure

```
outputs/llm_calls/<model>/<item_id>/
├── batch_20251011_143022_user_mattia/
│   ├── rep_1.json          # Scoring result repeat 1
│   ├── rep_2.json          # Scoring result repeat 2
│   ├── rep_3.json          # Scoring result repeat 3
│   └── batch_info.json     # Metadata (timestamp, user, hostname, config)
├── batch_20251011_150530_user_colleague/
│   ├── rep_1.json
│   ├── rep_2.json
│   ├── rep_3.json
│   └── batch_info.json
```

### Batch Metadata (batch_info.json)

```json
{
  "timestamp": "2025-10-11T14:30:22",
  "user": "mattia",
  "hostname": "mattia-pc",
  "model": "gemini-2.5-pro",
  "repeats": 3,
  "config_hash": "abc123...",
  "rubric_weights": {...},
  "temperature": 0.0,
  "top_p": 1.0
}
```

### Configuration Options

In `config.yaml` or `config.local.yaml`:
```yaml
scoring:
  use_batch_mode: true     # Enable/disable batch mode (default: true)
  results_dir: null        # null = local outputs/llm_calls
                           # or path to shared directory for multi-user
```

### CLI Usage

```bash
# Score with batch mode (default)
vfscore score --model gemini-2.5-pro --repeats 3

# Aggregate ALL batches (DEFAULT - recommended for best statistics)
vfscore aggregate

# Aggregate only latest batch
vfscore aggregate --latest-only

# Filter batches by user
vfscore aggregate --batch-pattern "user_mattia"

# Filter batches by date
vfscore aggregate --after 2025-10-01
```

### Multi-User Collaboration Workflow

**Option 1: Local merging (simple)**
1. User A runs scoring → creates batch locally
2. User B runs scoring → creates batch locally
3. Copy both `outputs/llm_calls/` folders to common location
4. Run `vfscore aggregate` - automatically merges all batches

**Option 2: Shared directory (advanced)**
```yaml
# In config.local.yaml
scoring:
  results_dir: "\\networkdrive\shared\vfscore"
```
All users write directly to shared location, no manual merging needed.

## Important Implementation Details

### scoring.py
- `create_batch_directory_name()`: Creates timestamped batch names
- `create_batch_metadata()`: Generates batch provenance information
- `run_scoring()`: Main orchestration, respects batch_mode config
- Model name normalization: `gemini-2.5-pro` → directory name `2_5_pro`

### aggregate.py
- `discover_batch_directories()`: Auto-discovers batches (new) or legacy structure
- `filter_batch_directories()`: Applies user filters (latest_only, pattern, date)
- `aggregate_item()`: Merges all batches for an item, computes statistics
- `run_aggregation()`: Main entry point, supports filtering options
- **Default behavior**: Aggregates ALL batches (not just latest)

### Key Files Modified (2025-10-11)
- `src/vfscore/config.py`: Added `use_batch_mode` and `results_dir` to ScoringConfig
- `src/vfscore/scoring.py`: Implemented batch directory creation and metadata
- `src/vfscore/aggregate.py`: Implemented batch discovery and multi-batch aggregation
- `src/vfscore/__main__.py`: Added CLI options for batch filtering
- `config.yaml`: Added batch mode configuration

## Output Files

### Per-run Outputs
- `outputs/llm_calls/<model>/<item_id>/batch_*/rep_*.json`: Raw LLM responses

### Aggregated Results
- `outputs/results/per_item.jsonl`: Detailed records (includes batch info)
- `outputs/results/per_item.csv`: Summary scores with columns:
  - Standard: item_id, l1, l2, l3, n_gt, final_score, confidence, mad
  - **New**: n_batches, n_total_repeats
  - Per-model: <model>_median
  - flags

## Virtual Environment

**IMPORTANT**: Use `venv/` (not `.venv/`)
- Location: `C:\Users\matti\OneDrive - Politecnico di Bari (1)\Dev\VFScore\venv\`
- Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
- Python: `venv\Scripts\python.exe`

## API Keys

Required in `.env` file:
- `GEMINI_API_KEY`: Google Gemini API key (required)
- `OPENAI_API_KEY`: OpenAI API key (optional, Phase 2)

Get Gemini key: https://aistudio.google.com/app/apikey

## Common Issues & Solutions

1. **"GEMINI_API_KEY not set"**: Ensure `.env` file exists with valid key
2. **"Blender not found"**: Update `blender_exe` in `config.local.yaml`
3. **Import errors**: Activate virtual environment
4. **Legacy results**: Old results without batch structure are treated as single "legacy" batch

## Development Guidelines

- Use `config.local.yaml` for machine-specific settings
- Never commit `.env`, `config.local.yaml`, or `outputs/`
- Batch mode is enabled by default - disable only for testing
- Aggregation defaults to ALL batches - use `--latest-only` sparingly

## Git Branch Info
- Main branch: `main`
- Recent commits focused on rate limiting, multiuser support, scoring parameters

## Phase Status
- ✅ Phase 1: Core pipeline complete
- 🔄 Phase 2: Sentinel trials, multi-model ensemble (in progress)
- ⏳ Phase 3: Web interface, cloud deployment (planned)

## Notes for Future Development

1. **Backward Compatibility**: The batch system is backward compatible with legacy results
2. **Statistical Rationale**: More batches = better statistical assessment (higher n_total_repeats)
3. **No Merge Conflicts**: Self-describing batches eliminate merge issues
4. **Provenance Tracking**: batch_info.json tracks who/when/how for reproducibility
5. **Flexible Aggregation**: Can analyze subsets of batches without losing data
