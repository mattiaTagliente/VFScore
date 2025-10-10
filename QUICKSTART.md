# VFScore Quick Reference

## Installation (One-Time Setup)

```powershell
# 1. Navigate to project
cd "C:\Users\matti\OneDrive - Politecnico di Bari (1)\Dev\VFScore"

# 2. Create virtual environment
python -m venv venv

# 3. Activate
.\venv\Scripts\activate

# 4. Install
pip install -e .

# 5. Configure API key
copy .env.example .env
notepad .env  # Add your GEMINI_API_KEY

# 6. Test setup
python tests\test_setup.py
```

## Daily Workflow

```powershell
# Activate virtual environment (if not already active)
.\venv\Scripts\activate

# Run complete pipeline
vfscore run-all

# Or run steps individually
vfscore ingest
vfscore preprocess-gt
vfscore render-cand
vfscore package
vfscore score
vfscore aggregate
vfscore report

# View results
start outputs\report\index.html
```

## Common Commands

### Fast Testing
```powershell
# Fast render mode (128 samples, ~2x faster)
vfscore run-all --fast

# Single repeat for quick testing
vfscore score --repeats 1

# Render only one step
vfscore render-cand --fast
```

### Different Models
```powershell
# Use Gemini (default)
vfscore score --model gemini

# Phase 2: GPT-4V support
# vfscore score --model gpt4v
```

### Re-run Specific Steps
```powershell
# Re-score with different parameters
vfscore score --repeats 5

# Regenerate report
vfscore report

# Re-aggregate with new scores
vfscore aggregate
```

## Configuration

Edit `config.yaml` to customize:

```yaml
# Rendering quality
render:
  samples: 256  # Increase for better quality, decrease for speed

# Scoring
scoring:
  repeats: 3  # Number of repeats per item
  temperature: 0.0  # LLM temperature

# Preprocessing
preprocess:
  canvas_px: 1024  # Output resolution
```

## Output Files

```
outputs/
├── manifest.jsonl                # Dataset index
├── preprocess/                   # Processed images
├── labels/                       # Labeled images for LLM
├── llm_calls/                    # Raw LLM responses
├── results/
│   ├── per_item.csv             # 📊 Import to Excel
│   └── per_item.jsonl           # 📝 Detailed records
└── report/
    └── index.html               # 🎨 Main report
```

## Troubleshooting

### "GEMINI_API_KEY not set"
```powershell
# Check .env file exists
dir .env

# Or set directly
$env:GEMINI_API_KEY="your_key_here"
```

### Rendering is slow
```powershell
# Use fast mode
vfscore render-cand --fast

# Or edit config.yaml
render:
  samples: 128  # Down from 256
```

### Out of memory
```powershell
# Process fewer items at once
# Or close other applications
# Or reduce render samples
```

### Background removal fails
```powershell
# First run downloads model (~176MB)
# Ensure internet connection
# Wait for download to complete
```

## Data Preparation

### Adding New Items

1. Add reference photos:
   ```
   datasets/refs/<item_id>/photo1.jpg
   datasets/refs/<item_id>/photo2.jpg
   ```

2. Add generated object:
   ```
   datasets/gens/<item_id>/object.glb
   ```

3. Update categories:
   ```
   metadata/categories.csv
   ```

4. Re-run pipeline:
   ```powershell
   vfscore run-all
   ```

### File Requirements

- **Photos**: JPG or PNG, any resolution, sRGB or convertible
- **3D Objects**: GLB format only
- **Categories**: CSV with columns: item_id, l1, l2, l3

## Performance Tips

### Speed vs Quality Trade-offs

| Mode | Samples | Time per Item | Quality |
|------|---------|---------------|---------|
| Fast | 128 | ~2-3 min | Good |
| Default | 256 | ~5-7 min | Excellent |
| High | 512 | ~15-20 min | Best |

### Parallel Processing (Future)
Currently sequential. Phase 2 will add parallel rendering.

## Git Workflow

```powershell
# Initialize repo (if not done)
git init
git add .
git commit -m "Initial VFScore setup"

# Add remote
git remote add origin <your-repo-url>
git push -u origin main

# Regular commits
git add .
git commit -m "Add new evaluation results"
git push
```

## API Costs

### Gemini 2.0 Flash (Free Tier)
- ✅ 15 requests/minute
- ✅ 1,500 requests/day
- ✅ Free tier should cover 100-500 items/day

### Estimated Usage
- 3 items × 3 repeats = 9 requests
- ~6 images per request (5 GT + 1 candidate)
- Well within free tier limits

## Getting Help

1. Check `SETUP.md` for detailed setup
2. Review `README.md` for overview
3. Run `python tests/test_setup.py` to diagnose
4. Check logs in `outputs/logs/` (Phase 2)

## Version Info

```powershell
vfscore --version
python --version
```

## Quick Health Check

```powershell
# Test each component
vfscore ingest  # Should complete in seconds
python tests\test_setup.py  # All tests should pass
```

---

**Phase 1 Status**: ✅ Complete and Production Ready
