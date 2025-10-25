# VFScore - Visual Fidelity Scoring for 3D Generated Objects

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Automated pipeline for evaluating the **visual fidelity** of generated 3D objects against real product photographs using multimodal LLMs.

---

## 🎯 Overview

VFScore provides an end-to-end system to:
- 📸 Process reference product photos (background removal, standardization)
- 🎨 Render generated 3D objects (.glb) with controlled lighting and camera
- 🤖 Score visual appearance fidelity (0.000-1.000) using LLM vision models
- 📊 Generate bilingual reports (English/Italian) with confidence metrics

**Key Feature**: Evaluates **appearance only** (color, materials, textures) - geometry quality is assessed separately.

---

## ✨ Features

- ⚡ **Automated Pipeline**: 8-step workflow from raw data to final report
- 🌍 **Bilingual Reports**: Interactive English/Italian reports with one-click language switching
- 🛡️ **Cost Protection**: Headless cost tracking with automatic limits (archi3D-compatible)
- 🚀 **Multi-Key Async**: Team collaboration with 5x speedup (5 API keys = 25 RPM, 500 RPD)
- 🔬 **Validation Studies**: Parameter sweep support with complete metadata tracking
- 🔄 **Batch System**: Multi-user collaboration without overwriting results
- 🎯 **Confidence Metrics**: Statistical validation with MAD-based confidence scores
- 🔧 **Configurable**: Flexible YAML configuration with machine-specific overrides
- ⚙️ **Production Ready**: Headless operation, error handling, rate limiting, progress tracking

---

## 🚀 Quick Start

### 1. Install

```bash
# Clone repository
git clone https://github.com/mattiaTagliente/VFScore.git
cd VFScore

# Run interactive setup
python setup.py
```

The setup script will:
- Create your `.env` file with API keys
- Configure Blender path automatically
- Install all dependencies
- Verify the installation

### 2. Run Pipeline

```bash
# Activate virtual environment
.\venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux

# Run complete pipeline
vfscore run-all
```

### 3. View Report

Open `outputs/report/index.html` in your browser. Toggle between English and Italian with one click!

---

## 📖 Documentation

- **[Complete Guide](GUIDE.md)** - Installation, usage, configuration, development
- **[Cost Protection Guide](COST_PROTECTION_GUIDE.md)** - Headless cost protection system
- **[Changelog](CHANGELOG.md)** - Version history and updates
- **[Claude Instructions](CLAUDE.md)** - Project-specific instructions for Claude Code

---

## 🎨 Usage Examples

### Complete Pipeline

```bash
# Run everything at once
vfscore run-all

# Fast mode for testing (lower render samples)
vfscore run-all --fast

# Skip translation
vfscore run-all --skip-translation
```

### Individual Steps

```bash
vfscore ingest              # 1. Scan datasets
vfscore preprocess-gt       # 2. Preprocess ground truth
vfscore render-cand         # 3. Render candidates
vfscore package             # 4. Create scoring packets
vfscore score               # 5. Score with LLM
vfscore aggregate           # 6. Aggregate scores
vfscore translate           # 7. Translate to Italian
vfscore report              # 8. Generate bilingual report
```

### Bilingual Translation

```bash
# Translate existing results
vfscore translate

# Force re-translation
vfscore translate --force

# Use different translation model
vfscore translate --model gemini-2.5-flash
```

### Common Options

```bash
# Use different scoring model
vfscore score --model gemini-2.5-flash

# More repeats for higher confidence
vfscore score --repeats 5

# Parameter sweep for validation studies
vfscore score --repeats 5 --temperature 0.5 --top-p 0.95

# Aggregate only latest batch
vfscore aggregate --latest-only

# Filter by user or date
vfscore aggregate --batch-pattern "user_mattia"
vfscore aggregate --after 2025-01-01
```

### Validation Studies

```bash
# Run parameter sweep for validation study
vfscore score --repeats 5 --temperature 0.0 --top-p 1.0  # Baseline
vfscore score --repeats 5 --temperature 0.5 --top-p 0.95 # Test setting

# Each evaluation gets unique run_id for statistical independence
# Complete metadata (temperature, top_p, run_id, timestamp) logged
```

See **[Validation Studies Guide](GUIDE.md#validation-studies)** for details.

---

## 📊 Scoring Rubric

Visual fidelity is evaluated across 4 weighted dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Color & Palette** | 40% | Overall hue, saturation, brightness |
| **Material Finish** | 25% | Metallic/dielectric, roughness, specular |
| **Texture Identity** | 15% | Correct patterns, logos, prints |
| **Texture Scale & Placement** | 20% | Scale, alignment, seams |

**Final Score** = Weighted sum [0.000-1.000]

**Note**: Geometry/silhouette is explicitly **excluded**.

---

## 🌍 Bilingual Reports

VFScore generates interactive bilingual reports:

- **English** and **Italian** versions side-by-side
- One-click language switching
- Automatic translation using Gemini 2.5 Flash
- Smart caching to avoid redundant translations
- Language preference saved in browser

**Example:**

```yaml
# Enable translation in config
translation:
  enabled: true
  model: gemini-2.5-flash
  cache_translations: true
```

---

## 🛡️ Cost Protection (Headless Mode)

VFScore includes **7 layers of cost protection** to prevent unexpected API charges:

1. **Pre-flight billing warning** (informational, no prompt)
2. **Cost estimation** before execution (USD and EUR)
3. **Configuration-based limit** (auto-abort if exceeded)
4. **Real-time cost tracking** during execution
5. **Threshold alerts** at $1, $5, $10, $20 (informational)
6. **Automatic stop** when `max_cost_usd` reached
7. **Final cost summary** with detailed logs

**Headless Operation**: No interactive prompts - suitable for archi3D integration and automated workflows.

**Example Configuration:**

```yaml
# config.local.yaml
scoring:
  max_cost_usd: 20.0  # Maximum $20 per run (auto-abort if exceeded)
  display_billing_warning: true
  display_cost_estimate: true
```

**CRITICAL**: Check your billing status at https://aistudio.google.com/ to avoid unexpected charges. See **[Cost Protection Guide](COST_PROTECTION_GUIDE.md)** for complete details.

---

## 🚀 Multi-Key Async Scoring

VFScore supports **team collaboration** with multiple API keys for dramatically faster scoring:

**Performance Scaling:**
- **1 key**: 5 RPM, 100 RPD (baseline)
- **5 keys**: 25 RPM, 500 RPD (5x faster!)
- **N keys**: Nx speedup, 100N requests/day

**Setup:**

```yaml
# config.local.yaml
scoring:
  use_async: true
  api_keys:
    - $GEMINI_API_KEY_USER1  # Your key
    - $GEMINI_API_KEY_USER2  # Team member 2
    - $GEMINI_API_KEY_USER3  # Team member 3
    - $GEMINI_API_KEY_USER4  # Team member 4
    - $GEMINI_API_KEY_USER5  # Team member 5
  key_labels:
    - mattia
    - user2
    - user3
    - user4
    - user5
  rpm_limit: 5       # Per-key limit
  tpm_limit: 125000  # Per-key limit
  rpd_limit: 100     # Per-key limit
```

```bash
# .env
GEMINI_API_KEY_USER1=your_key_here
GEMINI_API_KEY_USER2=colleague_key_here
# ... etc
```

**Features:**
- Intelligent round-robin key selection
- Per-key quota tracking (RPM, TPM, RPD)
- Automatic quota warnings at 80% daily usage
- Statistics export to `outputs/llm_calls/key_pool_stats.json`

**Compliance**: Fully compliant with Google ToS - designed for legitimate collaborative research teams.

---

## 🏗️ Project Structure

```
VFScore/
├── src/vfscore/          # Source code
│   ├── __main__.py       # CLI entry point
│   ├── config.py         # Configuration management
│   ├── scoring.py        # LLM scoring orchestration
│   ├── translate.py      # Translation orchestration
│   ├── report.py         # Bilingual report generation
│   └── llm/              # LLM client implementations
├── datasets/
│   ├── refs/             # Reference photos (GT)
│   └── gens/             # Generated .glb files
├── metadata/
│   └── categories.csv    # Item categories
├── assets/
│   └── lights.hdr        # Studio HDRI lighting
├── outputs/              # Generated artifacts (not in git)
│   ├── llm_calls/        # Scoring results + translations
│   ├── results/          # Aggregated scores
│   └── report/           # HTML reports
├── config.yaml           # Shared configuration
├── config.local.yaml     # Your local overrides (not in git)
└── .env                  # Your API keys (not in git)
```

---

## ⚙️ Prerequisites

- **Python 3.11+**
- **Blender 4.2+** ([Download](https://www.blender.org/download/))
- **Google Gemini API Key** ([Get Key](https://aistudio.google.com/app/apikey))

---

## 🔧 Configuration

VFScore uses a **two-layer configuration system**:

1. **`config.yaml`** - Shared defaults (committed to git)
2. **`config.local.yaml`** - Your machine-specific overrides (not committed)

**Example `config.local.yaml`:**

```yaml
paths:
  blender_exe: "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

render:
  samples: 128  # Lower for faster testing

translation:
  enabled: true  # Enable Italian translation
```

See **[Complete Guide](GUIDE.md)** for full configuration reference.

---

## 🤝 Contributing

We welcome contributions! See **[Contributing Guidelines](GUIDE.md#contributing)** in the Complete Guide.

**Quick Start for Contributors:**

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes and test: `vfscore run-all --fast`
4. Commit: `git commit -m "feat: your feature"`
5. Push and create Pull Request

---

## 🐛 Troubleshooting

### Common Issues

**"GEMINI_API_KEY not set"**
→ Create `.env` file with your API key. Run `python setup.py` to set up interactively.

**"Blender not found"**
→ Set `blender_exe` path in `config.local.yaml`. Run `python setup.py` to auto-detect.

**Translation not showing**
→ Verify `translation.enabled: true` in config and run `vfscore translate`.

See **[Troubleshooting Guide](GUIDE.md#troubleshooting)** for more solutions.

---

## 📈 Roadmap

- [x] **Phase 1**: Core pipeline, LLM scoring, bilingual reports ✅
- [ ] **Phase 2**: Sentinel trials, multi-model ensemble, enhanced reporting
- [ ] **Phase 3**: Web interface, cloud deployment, advanced analytics

---

## 📝 Citation

If you use VFScore in your research, please cite:

```bibtex
@software{vfscore2025,
  title={VFScore: Automated Visual Fidelity Scoring for 3D Generation},
  author={Tagliente, Mattia},
  year={2025},
  url={https://github.com/mattiaTagliente/VFScore}
}
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 📞 Contact

- **GitHub**: [github.com/mattiaTagliente/VFScore](https://github.com/mattiaTagliente/VFScore)
- **Issues**: [github.com/mattiaTagliente/VFScore/issues](https://github.com/mattiaTagliente/VFScore/issues)

---

## 🙏 Acknowledgments

Built with:
- 🐍 Python
- 🎨 Blender Cycles
- 🤖 Google Gemini
- ☕️ Lots of coffee

---

**Ready to get started?** Check out the **[Complete Guide](GUIDE.md)**! 🚀
