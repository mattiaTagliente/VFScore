# VFScore Setup Guide

## Phase 1 Implementation - Complete ✅

This guide will help you set up and run VFScore on your Windows 11 system.

## Prerequisites

✅ **Already Installed:**
- Python 3.11
- Blender 4.5 at `C:\Program Files\Blender Foundation\Blender 4.5`
- Data structure in place (datasets/, metadata/, assets/)

❓ **Need to Obtain:**
- Google Gemini API key

## Installation Steps

### 1. Create Virtual Environment

Open PowerShell or Command Prompt in the project directory:

```powershell
cd "C:\Users\matti\OneDrive - Politecnico di Bari (1)\Dev\VFScore"

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\activate
```

### 2. Install Dependencies

```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install the package in editable mode
pip install -e .

# OR install from requirements.txt
pip install -r requirements.txt
```

**Note:** Installation may take a few minutes, especially for:
- `rembg` (background removal - includes U²-Net model)
- `opencv-python` (computer vision)
- `google-generativeai` (Gemini API)

### 3. Configure API Keys

```powershell
# Copy the example environment file
copy .env.example .env

# Edit .env with your favorite editor (Notepad, VS Code, etc.)
notepad .env
```

Add your Gemini API key:
```
GEMINI_API_KEY=your_actual_api_key_here
```

**Get Gemini API Key:**
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy and paste into .env file

### 4. Verify Installation

```powershell
# Check if CLI is available
vfscore --version

# Should output: VFScore version 0.1.0
```

## Running the Pipeline

### Option A: Run All Steps at Once

```powershell
vfscore run-all --model gemini --repeats 3
```

This will execute:
1. Ingest data
2. Preprocess GT photos
3. Render candidates
4. Package scoring units
5. Score with Gemini (3 repeats)
6. Aggregate scores
7. Generate HTML report

### Option B: Run Steps Individually

```powershell
# Step 1: Ingest data
vfscore ingest

# Step 2: Preprocess ground truth photos
vfscore preprocess-gt

# Step 3: Render candidates (may take 5-10 min per item)
vfscore render-cand

# Optional: Fast mode with fewer samples
vfscore render-cand --fast

# Step 4: Package scoring units
vfscore package

# Step 5: Score with LLM (requires API key)
vfscore score --model gemini --repeats 3

# Step 6: Aggregate results
vfscore aggregate

# Step 7: Generate report
vfscore report
```

## Output Files

After running the pipeline, check these directories:

```
outputs/
├── manifest.jsonl                     # Ingested data summary
├── preprocess/
│   ├── refs/<item_id>/gt_*.png       # Processed GT images
│   └── cand/<item_id>/candidate.png  # Rendered candidates
├── labels/<item_id>/                 # Labeled images for LLM
├── llm_calls/<model>/<item_id>/      # Raw LLM responses
├── results/
│   ├── per_item.csv                  # Summary CSV
│   └── per_item.jsonl                # Detailed JSON
└── report/
    └── index.html                    # 🎉 Open this in browser!
```

## Viewing Results

Open the HTML report:

```powershell
# Windows: Open with default browser
start outputs\report\index.html

# Or navigate to the file and double-click
```

## Troubleshooting

### Issue: "GEMINI_API_KEY environment variable not set"

**Solution:**
1. Make sure you created `.env` file (not `.env.example`)
2. Check that API key is correctly formatted
3. Try setting it directly in PowerShell:
   ```powershell
   $env:GEMINI_API_KEY="your_key_here"
   vfscore score
   ```

### Issue: "Blender not found"

**Solution:**
Check `config.yaml` has correct path:
```yaml
paths:
  blender_exe: "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe"
```

### Issue: Rendering is slow

**Solutions:**
- Use `--fast` flag for 128 samples instead of 256
- Close other GPU-intensive applications
- Check GPU is being used (Blender should auto-detect)

### Issue: Background removal fails

**Solution:**
First run will download the U²-Net model (~176MB). Ensure internet connection is available.

### Issue: "No module named 'vfscore'"

**Solution:**
Make sure you're in the project directory and virtual environment is activated:
```powershell
cd "C:\Users\matti\OneDrive - Politecnico di Bari (1)\Dev\VFScore"
.\venv\Scripts\activate
pip install -e .
```

## Performance Tips

### For Testing (Fast Mode)
- Use `--fast` for rendering (128 samples)
- Reduce `repeats` to 1 or 2 for initial testing
- Test with a single item first

### For Production (High Quality)
- Use default samples (256) for best quality
- Use 3 repeats for reliable confidence metrics
- Run on a machine with good GPU for faster rendering

## API Rate Limits

**Gemini 2.0 Flash:**
- Free tier: 15 requests per minute
- For 3 items × 3 repeats = 9 requests (< 1 minute)
- Exponential backoff is implemented for rate limit handling

## Cost Estimation

**Gemini 2.0 Flash (as of 2025):**
- Free tier available with generous limits
- ~6 images per request (5 GT + 1 candidate)
- 3 items × 3 repeats = 9 API calls
- Should be within free tier for small datasets

## Next Steps

After successful Phase 1 run:

1. **Analyze Results:**
   - Review HTML report for visual assessment
   - Check CSV for statistical analysis
   - Look for patterns in low/high scores

2. **Iterate:**
   - Adjust rendering parameters in `config.yaml`
   - Tune rubric weights if needed
   - Add more items to dataset

3. **Phase 2 (Future):**
   - Sentinel trials for quality control
   - GPT-4V multi-model ensemble
   - Advanced confidence metrics
   - Enhanced HTML reporting

## Need Help?

- Check logs in `outputs/logs/` directory
- Review configuration in `config.yaml`
- Ensure all paths are correct
- Verify API key is valid

## Quick Test

Test with a single command:

```powershell
vfscore ingest
```

If this completes successfully, you're ready to run the full pipeline!

---

**Phase 1 Status: ✅ Complete and Ready to Use**
