# 📋 VFScore First Run Checklist

Use this checklist to ensure everything is set up correctly before your first pipeline run.

---

## ☑️ Pre-Installation

- [ ] Windows 11 Pro 64-bit (confirmed ✅)
- [ ] Python 3.11 installed (confirmed ✅)
- [ ] Blender 4.5 at `C:\Program Files\Blender Foundation\Blender 4.5` (confirmed ✅)
- [ ] Internet connection (for downloading segmentation models)
- [ ] ~5 GB free disk space for outputs

---

## ☑️ Installation Steps

### 1. Virtual Environment
```powershell
cd "C:\Users\matti\OneDrive - Politecnico di Bari (1)\Dev\VFScore"
```

- [ ] Navigate to project directory
- [ ] Create venv: `python -m venv venv`
- [ ] Activate venv: `.\venv\Scripts\activate`
- [ ] Verify activation (prompt shows `(venv)`)

### 2. Dependencies
```powershell
pip install --upgrade pip
pip install -e .
```

- [ ] Upgrade pip
- [ ] Install package in editable mode
- [ ] Wait for installation (~5-10 minutes)
- [ ] No error messages during installation

**Expected packages** (~1 GB total):
- typer, pydantic, pyyaml
- pillow, numpy, opencv-python
- google-generativeai
- rembg (includes U²-Net model)
- tqdm, rich, jinja2

### 3. API Configuration
```powershell
copy .env.example .env
notepad .env
```

- [ ] Copy `.env.example` to `.env`
- [ ] Get Gemini API key from https://aistudio.google.com/app/apikey
- [ ] Paste API key in `.env` file
- [ ] Save and close `.env` file
- [ ] Verify file exists: `dir .env`

---

## ☑️ Verification

### Run Setup Test
```powershell
python tests\test_setup.py
```

**Expected output**:
- [ ] ✓ Python Version: 3.11.x
- [ ] ✓ All package imports successful
- [ ] ✓ VFScore package loaded
- [ ] ✓ config.yaml loaded
- [ ] ✓ All required paths exist
- [ ] ✓ Blender executable found
- [ ] ✓ GEMINI_API_KEY set (masked)
- [ ] ✓ Dataset structure OK (3 items)

**If all tests pass**: ✅ Ready to run!

**If tests fail**: Review SETUP.md for troubleshooting

### Quick Command Test
```powershell
vfscore --version
```

- [ ] Command runs successfully
- [ ] Shows: `VFScore version 0.1.0`

---

## ☑️ Data Verification

### Check Dataset Structure
```powershell
dir datasets\refs
dir datasets\gens
dir metadata\categories.csv
dir assets\lights.hdr
```

**Expected structure**:
- [ ] `datasets/refs/558736/` has 1 photo
- [ ] `datasets/refs/709360/` has 1 photo
- [ ] `datasets/refs/737048/` has 1 photo
- [ ] `datasets/gens/558736/` has 1 .glb file
- [ ] `datasets/gens/709360/` has 1 .glb file
- [ ] `datasets/gens/737048/` has 1 .glb file
- [ ] `metadata/categories.csv` exists and has 3 rows
- [ ] `assets/lights.hdr` exists

---

## ☑️ First Run (Test Mode)

### Run Single Item Test
```powershell
# Test with fast mode and single repeat
vfscore run-all --fast --repeats 1
```

**What happens** (approx. 5-10 minutes total):

1. **Ingest** (~1 second)
   - [ ] Scans datasets
   - [ ] Creates manifest.jsonl
   - [ ] Shows: "Manifest created with 3 items"

2. **Preprocess GT** (~30 seconds)
   - [ ] Downloads U²-Net model (first run only, ~176MB)
   - [ ] Processes 3 photos
   - [ ] Progress bar reaches 100%
   - [ ] Shows: "Processed 3/3 images"

3. **Render Candidates** (~6-9 minutes total, ~2-3 min per item)
   - [ ] Blender runs in background (3 times)
   - [ ] Progress bar advances
   - [ ] Shows: "Successfully rendered 3/3 objects"

4. **Package** (~1 second)
   - [ ] Creates labeled images
   - [ ] Shows: "Successfully created 3/3 packets"

5. **Score** (~10-15 seconds total, 1 repeat per item)
   - [ ] Calls Gemini API (3 times)
   - [ ] Progress bar advances
   - [ ] Shows: "Completed 3 API calls for 3/3 items"

6. **Aggregate** (~1 second)
   - [ ] Computes statistics
   - [ ] Creates CSV and JSONL
   - [ ] Shows summary statistics

7. **Report** (~5 seconds)
   - [ ] Generates HTML
   - [ ] Shows: "Report saved: outputs\report\index.html"

**Success indicators**:
- [ ] ✓ symbols for each completed step
- [ ] No red ✗ error messages
- [ ] "Pipeline complete!" message

---

## ☑️ Results Verification

### Check Output Files
```powershell
dir outputs
start outputs\report\index.html
```

**Expected outputs**:
- [ ] `outputs/manifest.jsonl` (3 lines)
- [ ] `outputs/preprocess/refs/558736/gt_1.png`
- [ ] `outputs/preprocess/refs/709360/gt_1.png`
- [ ] `outputs/preprocess/refs/737048/gt_1.png`
- [ ] `outputs/preprocess/cand/558736/candidate.png`
- [ ] `outputs/preprocess/cand/709360/candidate.png`
- [ ] `outputs/preprocess/cand/737048/candidate.png`
- [ ] `outputs/labels/*/packet.json` (3 items)
- [ ] `outputs/llm_calls/gemini/*/rep_1.json` (3 items)
- [ ] `outputs/results/per_item.csv`
- [ ] `outputs/results/per_item.jsonl`
- [ ] `outputs/report/index.html` ✨

### View HTML Report
```powershell
start outputs\report\index.html
```

**Report should show**:
- [ ] Header with "VFScore Report"
- [ ] Summary statistics (3 items, mean/median scores)
- [ ] 3 item cards with:
  - [ ] GT images (1 per item)
  - [ ] Candidate image
  - [ ] Score circle (0-100)
  - [ ] Confidence badge
  - [ ] Subscores bars
  - [ ] Rationale bullets

### Check CSV Results
```powershell
start outputs\results\per_item.csv
```

**CSV should have**:
- [ ] Header row with columns: item_id, l1, l2, l3, n_gt, final_score, confidence, etc.
- [ ] 3 data rows (one per item)
- [ ] Scores in range 0-100
- [ ] Confidence in range 0-1

---

## ☑️ Production Run

### Run Full Pipeline
```powershell
# Full quality: 256 samples, 3 repeats
vfscore run-all
```

**Time estimate**: ~30-45 minutes total for 3 items
- Rendering: ~15-21 minutes (3 items × 5-7 min)
- Scoring: ~30-45 seconds (9 API calls total)
- Other steps: ~1-2 minutes

**During execution**:
- [ ] GPU usage visible (Task Manager → Performance → GPU)
- [ ] Progress bars update smoothly
- [ ] No timeout errors
- [ ] No rate limit errors (should be within free tier)

---

## ☑️ Post-Run Checklist

### Verify Results
- [ ] All 3 items have scores
- [ ] Scores are reasonable (not all 0 or 100)
- [ ] Confidence values > 0.5 (good agreement)
- [ ] Rationales make sense
- [ ] Images look correct in report

### Save Results
```powershell
# Optional: Copy results for backup
copy outputs\results\per_item.csv results_backup_2025-01-10.csv
```

- [ ] Results backed up
- [ ] HTML report saved/shared if needed

### Git Commit (Optional)
```powershell
git add .
git commit -m "Initial VFScore run - 3 items completed"
```

- [ ] Code committed
- [ ] Results documented

---

## ☑️ Troubleshooting

If something goes wrong:

### Check 1: Environment
```powershell
.\venv\Scripts\activate
python --version  # Should be 3.11.x
pip list  # Should show all packages
```

### Check 2: API Key
```powershell
# In PowerShell
$env:GEMINI_API_KEY
# Should show your key (or check .env file)
```

### Check 3: Paths
```powershell
python tests\test_setup.py
# All tests should pass
```

### Check 4: Logs
```powershell
# Check Blender output if rendering fails
# Errors are shown in console during render
```

---

## ✅ Success Criteria

**You're successful if**:
- [x] `python tests\test_setup.py` shows all ✓
- [x] `vfscore run-all` completes without errors
- [x] HTML report opens and looks good
- [x] CSV has 3 rows with reasonable scores
- [x] All output files exist

**Congratulations! 🎉 VFScore is working!**

---

## 📞 Need Help?

1. **Re-read documentation**:
   - `SETUP.md` - Detailed setup
   - `QUICKSTART.md` - Common commands
   - `PROJECT_STATUS.md` - Implementation details

2. **Run diagnostics**:
   ```powershell
   python tests\test_setup.py
   ```

3. **Check configuration**:
   ```powershell
   notepad config.yaml
   notepad .env
   ```

4. **Review outputs**:
   ```powershell
   dir outputs
   ```

---

## 🎯 Next Steps After First Run

1. **Analyze results**:
   - Review scores in CSV
   - Check HTML report visually
   - Note any patterns or outliers

2. **Tune if needed**:
   - Adjust rubric weights in `config.yaml`
   - Test different render samples
   - Try different LLM temperatures

3. **Expand dataset**:
   - Add more items
   - Re-run pipeline
   - Compare results

4. **Document findings**:
   - Save interesting results
   - Share reports with team
   - Plan improvements

---

**Ready? Let's go! 🚀**

```powershell
python tests\test_setup.py
vfscore run-all --fast  # First test run
```
