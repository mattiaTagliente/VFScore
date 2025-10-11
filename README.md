# VFScore - Visual Fidelity Scoring for 3D Generated Objects

Automated pipeline for evaluating the visual fidelity of generated 3D objects against real product photographs using multimodal LLMs.

## Overview

VFScore provides an end-to-end system to:
- Process reference product photos (remove backgrounds, standardize format)
- Render generated 3D objects (.glb) with controlled lighting and camera
- Score visual appearance fidelity (0-100) using LLM vision models
- Generate comprehensive reports with confidence metrics

**Key Feature**: Evaluates appearance only (color, materials, textures) - geometry quality is assessed separately using F-SCORE.

## Project Structure

```
VFScore/
├── src/vfscore/          # Source code
│   ├── __main__.py       # CLI entry point
│   ├── config.py         # Configuration management
│   ├── ingest.py         # Data ingestion
│   ├── preprocess_gt.py  # GT photo preprocessing
│   ├── render_cycles.py  # Blender Cycles rendering
│   ├── preprocess_cand.py# Candidate preprocessing
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
├── outputs/              # Generated artifacts
└── tests/                # Unit tests

## Installation

### Prerequisites
- Python 3.11+
- Blender 4.5+ installed at: `C:\Program Files\Blender Foundation\Blender 4.5\blender.exe`
- API keys for LLM services (Gemini, GPT-4V)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd VFScore
```

2. Create virtual environment:
```bash
python -m venv venv
.\.venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -e .
# or
pip install -r requirements.txt
```

4. Set environment variables:
```bash
# Create .env file
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Quick Start

### Phase 1: Core Pipeline

Run the complete pipeline:

```bash
# 1. Ingest data and create manifest
vfscore ingest

# 2. Preprocess ground truth photos
vfscore preprocess-gt

# 3. Render candidate objects
vfscore render-cand

# 4. Package scoring units
vfscore package

# 5. Score with LLM
vfscore score --model gemini --repeats 3

# 6. Aggregate scores
vfscore aggregate

# 7. Generate report
vfscore report
```

Or run all steps at once:
```bash
vfscore run-all
```

## Configuration

Edit `vfscore/config.yaml` to customize:
- Camera positions and rendering settings
- LLM model selection and parameters
- Scoring rubric weights
- Output formats

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

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
ruff check src/
```

### Type Checking
```bash
mypy src/
```

## Roadmap

- [x] Phase 1: Core pipeline (preprocessing, rendering, LLM scoring, basic reports)
- [ ] Phase 2: Sentinel trials, confidence metrics, full HTML reporting
- [ ] Phase 3: Multi-model ensemble, advanced QC, optimization

## License

MIT License

## Citation

If you use VFScore in your research, please cite:

```bibtex
@software{vfscore2025,
  title={VFScore: Automated Visual Fidelity Scoring for 3D Generation},
  author={Francesca Falcone and Mattia Tagliente},
  year={2025},
  url={https://github.com/mattiatagliente/VFScore}
}
```

## Support

For issues and questions, please open a GitHub issue.