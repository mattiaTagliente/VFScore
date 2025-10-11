# Contributing to VFScore

Thank you for your interest in contributing to VFScore! This document provides guidelines and setup instructions for developers.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Configuration System](#configuration-system)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

---

## Getting Started

### Prerequisites

- **Python 3.11+** installed and accessible from command line
- **Blender 4.2+** installed (required for rendering)
- **Git** for version control
- **API Keys**: Gemini API key (required), OpenAI key (optional, Phase 2)

### Quick Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mattiaTagliente/VFScore.git
   cd VFScore
   ```

2. **Run the interactive setup:**
   ```bash
   python setup.py
   ```
   
   The setup script will:
   - Create your `.env` file with API keys
   - Create `config.local.yaml` with machine-specific settings
   - Auto-detect your Blender installation
   - Install Python dependencies
   - Verify the setup

3. **Activate virtual environment:**
   ```bash
   # Windows
   .\venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Test the installation:**
   ```bash
   vfscore --version
   python tests/test_setup.py
   ```

---

## Development Setup

### Manual Setup (Alternative)

If you prefer manual setup or the interactive script doesn't work:

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\activate on Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. **Create `config.local.yaml`:**
   ```yaml
   # config.local.yaml
   paths:
     blender_exe: "YOUR_BLENDER_PATH_HERE"
   
   # Optional: customize render settings
   render:
     samples: 128  # Lower for faster testing
   ```

### Environment Variables

The `.env` file should contain:

```bash
# Required
GEMINI_API_KEY=your_actual_gemini_api_key

# Optional (Phase 2)
OPENAI_API_KEY=your_actual_openai_api_key
```

**Important**: Never commit `.env` or `config.local.yaml` to git!

---

## Project Structure

```
VFScore/
├── src/vfscore/              # Main package source
│   ├── __main__.py          # CLI entry point
│   ├── config.py            # Configuration management
│   ├── ingest.py            # Data ingestion
│   ├── preprocess_gt.py     # GT preprocessing
│   ├── render_cycles.py     # Blender rendering
│   ├── packetize.py         # Scoring packets
│   ├── scoring.py           # LLM scoring
│   ├── aggregate.py         # Score aggregation
│   ├── report.py            # Report generation
│   └── llm/                 # LLM client implementations
│       ├── base.py          # Abstract client
│       └── gemini.py        # Gemini client
├── tests/                    # Test files
├── datasets/                 # Data (not in git)
├── metadata/                 # Category metadata
├── assets/                   # HDRI lighting
├── outputs/                  # Generated outputs (not in git)
├── config.yaml               # Shared default config (commit)
├── config.local.yaml         # Your local config (DO NOT commit)
├── .env                      # Your API keys (DO NOT commit)
├── setup.py                  # Interactive setup script
└── README.md                 # Documentation
```

---

## Configuration System

VFScore uses a **two-layer configuration system**:

### 1. `config.yaml` (Shared)
- **Purpose**: Default settings shared by all developers
- **Commit to git**: ✅ Yes, always commit
- **Contents**: Default render settings, rubric weights, paths

### 2. `config.local.yaml` (Personal)
- **Purpose**: Machine-specific overrides (Blender path, custom settings)
- **Commit to git**: ❌ Never commit (in .gitignore)
- **Contents**: Your Blender path, custom render samples, etc.

**How it works:**
1. VFScore loads `config.yaml` first
2. If `config.local.yaml` exists, its values override the defaults
3. This allows personalization without modifying shared settings

**Example `config.local.yaml`:**
```yaml
paths:
  blender_exe: "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

render:
  samples: 128  # Lower for faster development

logging:
  level: DEBUG  # More verbose logging
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clear, documented code
- Follow the existing code style
- Add tests for new functionality

### 3. Test Your Changes

```bash
# Run setup verification
python tests/test_setup.py

# Test specific commands
vfscore ingest
vfscore preprocess-gt --help

# Run full pipeline on test data
vfscore run-all --fast
```

### 4. Commit Your Changes

```bash
git add <files>
git commit -m "feat: add new feature"
```

**Commit message format:**
- `feat: ` - New feature
- `fix: ` - Bug fix
- `docs: ` - Documentation changes
- `refactor: ` - Code refactoring
- `test: ` - Adding tests
- `chore: ` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

## Code Style

### Python Style Guidelines

We follow **PEP 8** with some modifications:

- **Line length**: 100 characters (not 79)
- **Quotes**: Double quotes for strings
- **Type hints**: Always use type hints
- **Docstrings**: Google-style docstrings

### Formatting Tools

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

### Example Code Style

```python
"""Module docstring."""

from pathlib import Path
from typing import Dict, List


def process_items(items: List[str], config: Dict[str, any]) -> int:
    """Process a list of items.
    
    Args:
        items: List of item IDs to process
        config: Configuration dictionary
        
    Returns:
        Number of successfully processed items
        
    Raises:
        ValueError: If items list is empty
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    
    count = 0
    for item in items:
        if _process_single_item(item, config):
            count += 1
    
    return count
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test
python tests/test_setup.py

# Run with coverage
pytest --cov=vfscore tests/
```

### Writing Tests

Tests should be placed in `tests/` directory:

```python
# tests/test_ingest.py
import pytest
from vfscore.ingest import scan_references


def test_scan_references():
    """Test reference scanning."""
    refs_dir = Path("test_data/refs")
    result = scan_references(refs_dir)
    
    assert len(result) > 0
    assert "item_001" in result
```

---

## Pull Request Process

### Before Submitting

1. ✅ Code follows style guidelines
2. ✅ Tests pass
3. ✅ Documentation updated (if needed)
4. ✅ Commit messages are clear
5. ✅ No sensitive data committed (API keys, local paths)

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
How was this tested?

## Checklist
- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes
```

### Review Process

1. Submit PR on GitHub
2. Automated tests run (CI/CD)
3. Code review by maintainers
4. Address review comments
5. PR merged after approval

---

## Common Development Tasks

### Adding a New LLM Model

1. Create new client in `src/vfscore/llm/`:
   ```python
   # src/vfscore/llm/gpt4v.py
   from vfscore.llm.base import BaseLLMClient
   
   class GPT4VClient(BaseLLMClient):
       def score_visual_fidelity(self, ...):
           # Implementation
           pass
   ```

2. Update `scoring.py` to support the new model

3. Update documentation and tests

### Modifying the Rubric

1. Update rubric weights in `config.yaml`
2. Update prompts in `src/vfscore/llm/base.py`
3. Update documentation in `README.md`
4. Update tests if needed

### Adding New CLI Commands

1. Add command in `src/vfscore/__main__.py`:
   ```python
   @app.command()
   def my_command(
       param: str = typer.Option("default", help="Help text")
   ) -> None:
       """Command description."""
       # Implementation
       pass
   ```

2. Update documentation

---

## Troubleshooting

### Setup Issues

**Problem**: `GEMINI_API_KEY not set`
**Solution**: Ensure `.env` file exists with your API key

**Problem**: `Blender not found`
**Solution**: Update `blender_exe` path in `config.local.yaml`

**Problem**: `Import error: vfscore`
**Solution**: Run `pip install -e .` from project root

### Git Issues

**Problem**: Accidentally committed `.env`
**Solution**:
```bash
git rm --cached .env
git commit -m "Remove .env from git"
```

**Problem**: Merge conflicts in `config.yaml`
**Solution**: Keep your changes in `config.local.yaml` instead

---

## Getting Help

- 📖 Read the documentation in `README.md` and `SETUP.md`
- 🐛 Check existing [GitHub Issues](https://github.com/mattiaTagliente/VFScore/issues)
- 💬 Create a new issue with:
  - Clear description
  - Steps to reproduce
  - System information
  - Error messages/logs

---

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on the code, not the person
- Provide helpful feedback

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to VFScore!** 🎉
