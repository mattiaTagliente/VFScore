# VFScore - Visual Fidelity Scoring for 3D Generated Objects

Automated pipeline for evaluating the visual fidelity of generated 3D objects against real product photographs using multimodal LLMs.

## Overview

VFScore provides an end-to-end system to:
- Process reference product photos (remove backgrounds, standardize format)
- Render generated 3D objects (.glb) with controlled lighting and camera
- Score visual appearance fidelity (0-100) using LLM vision models
- Generate comprehensive reports with confidence metrics

**Key Feature**: Evaluates appearance only (color, materials, textures) - geometry quality is assessed separately using F-SCORE.

## Quick Start

### For New Developers

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mattiaTagliente/VFScore.git
   cd VFScore
   ```

2. **Run interactive setup:**
   ```bash
   python setup.py
   ```
   
   The setup script will guide you through:
   - Creating your `.env` file with API keys
   - Configuring Blender path
   - Installing dependencies
   - Verifying the setup

3. **Activate virtual environment:**
   ```bash
   # Windows
   .\venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Run the pipeline:**
   ```bash
   vfscore run-all
   ```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed developer setup instructions.

## Project Structure

```
VFScore/
├── src/vfscore/          # Source code
│   ├── __main__.py       # CLI entry point
│   ├── config.py         # Configuration management
│   ├── ingest.py         # Data ingestion
│   ├── preprocess_gt.py  # GT photo preprocessing
│   ├── render_cycles.py  # Blender Cycles rendering
│   ├── packetize.py      # Scoring packet assembly
│   ├── scoring.py        # LLM scoring orchestration
│   ├── aggregate.py      # Score aggregation
│   ├── report.py         # Report generation
│   └── llm/              # LLM client implementations
├── datasets/
│   ├── refs/             # Reference photos (GT)
│   └── gens/             # Generated .glb files
├── metadata/
│   └── categories.csv    # Item categories (l1, l2, l3)
├── assets/
│   └── lights.hdr        # Studio HDRI lighting
├── outputs/              # Generated artifacts (not in git)
├── tests/                # Unit tests
├── config.yaml           # Shared default config
├── config.local.yaml     # Your local overrides (not in git)
├── .env                  # Your API keys (not in git)
└── setup.py              # Interactive setup script
```

## Configuration System

VFScore uses a two-layer configuration approach:

- **`config.yaml`**: Shared default settings (committed to git)
- **`config.local.yaml`**: Your machine-specific overrides (not committed)

Example `config.local.yaml`:
```yaml
paths:
  blender_exe: "/your/path/to/blender"

render:
  samples: 128  # Lower for faster testing
```

## Prerequisites

- **Python 3.11+**
- **Blender 4.2+** for rendering
- **Git** for version control
- **API Keys**:
  - Google Gemini API key (required) - Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
  - OpenAI API key (optional, for Phase 2)

## Installation

### Option 1: Interactive Setup (Recommended)

```bash
python setup.py
```

### Option 2: Manual Setup

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Create configuration:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. Create local config:
   ```yaml
   # config.local.yaml
   paths:
     blender_exe: "YOUR_BLENDER_PATH"
   ```

See [SETUP.md](SETUP.md) for detailed installation guide.

## Usage

### Complete Pipeline

```bash
# Run all steps at once
vfscore run-all

# Or run steps individually:
vfscore ingest              # 1. Scan dataset
vfscore preprocess-gt       # 2. Preprocess GT photos
vfscore render-cand         # 3. Render candidates
vfscore package             # 4. Create scoring packets
vfscore score               # 5. Score with LLM
vfscore aggregate           # 6. Aggregate scores
vfscore report              # 7. Generate HTML report
```

### Common Options

```bash
# Fast rendering mode (128 samples instead of 256)
vfscore run-all --fast

# Use different model
vfscore score --model gemini-2.5-flash

# More repeats for higher confidence
vfscore score --repeats 5

# View help
vfscore --help
vfscore score --help
```

## Scoring Rubric

Visual fidelity is evaluated across 4 dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Color & Palette | 40% | Overall hue, saturation, brightness |
| Material Finish | 25% | Metallic/dielectric, roughness, specular |
| Texture Identity | 15% | Correct patterns, logos, prints |
| Texture Scale & Placement | 20% | Scale, alignment, seams |

**Final Score**: Weighted sum [0-100]

## Output Files

```
outputs/
├── preprocess/
│   ├── refs/<item_id>/gt_*.png       # Processed GT images
│   └── cand/<item_id>/candidate.png  # Rendered candidates
├── labels/<item_id>/                 # Labeled images for LLM
├── llm_calls/<model>/<item_id>/      # Raw LLM responses
├── results/
│   ├── per_item.csv                  # Summary scores
│   └── per_item.jsonl                # Detailed records
└── report/
    └── index.html                    # Visual audit report
```

## Development

### Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code style guidelines
- Testing procedures
- Pull request process

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
ruff check src/
mypy src/
```

## Documentation

- [SETUP.md](SETUP.md) - Detailed setup guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Developer guide
- [QUICKSTART.md](QUICKSTART.md) - Quick reference
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Implementation status

## Roadmap

- [x] Phase 1: Core pipeline (preprocessing, rendering, LLM scoring, basic reports)
- [ ] Phase 2: Sentinel trials, multi-model ensemble, enhanced reporting
- [ ] Phase 3: Web interface, cloud deployment, advanced analytics

## Troubleshooting

### Common Issues

**"GEMINI_API_KEY not set"**
- Ensure `.env` file exists with your API key
- Run `python setup.py` to create it interactively

**"Blender not found"**
- Update `blender_exe` path in `config.local.yaml`
- Run `python setup.py` to auto-detect Blender

**Import errors**
- Make sure virtual environment is activated
- Run `pip install -e .` from project root

See [CONTRIBUTING.md](CONTRIBUTING.md) for more troubleshooting tips.

## License

MIT License - see LICENSE file for details.

## Citation

If you use VFScore in your research, please cite:

```bibtex
@software{vfscore2025,
  title={VFScore: Automated Visual Fidelity Scoring for 3D Generation},
  author={Tagliente, Mattia},
  year={2025},
  url={https://github.com/mattiaTagliente/VFScore}
}
```

## Contact

- **GitHub**: [github.com/mattiaTagliente/VFScore](https://github.com/mattiaTagliente/VFScore)
- **Issues**: [github.com/mattiaTagliente/VFScore/issues](https://github.com/mattiaTagliente/VFScore/issues)

## Acknowledgments

Built with Python, Blender, Google Gemini, and lots of ☕️
