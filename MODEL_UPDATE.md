# 🔧 Important Update - Model Correction

## Issue Fixed
Changed from **Gemini 2.0 Flash** to **Gemini 2.5 Pro** for visual fidelity scoring.

## Why This Change?

### Original (Incorrect)
- **Model**: `gemini-2.0-flash-exp`
- **Best for**: Speed and cost efficiency
- **Not ideal for**: Complex multi-image visual reasoning

### Updated (Correct) ✅
- **Model**: `gemini-2.5-pro`
- **Best for**: Complex reasoning, large context, detailed analysis
- **Perfect for**: Visual fidelity scoring with 6 images (5 GT + 1 candidate) and nuanced 6-dimension evaluation

## What Changed

### Files Updated:
1. ✅ `src/vfscore/llm/gemini.py` - Default model → `gemini-2.5-pro`
2. ✅ `config.yaml` - Model specification → `gemini-2.5-pro`
3. ✅ `src/vfscore/scoring.py` - Model handling and defaults
4. ✅ `src/vfscore/__main__.py` - CLI default → `gemini-2.5-pro`

### Key Improvements:
- **Better reasoning**: Gemini 2.5 Pro provides more nuanced visual analysis
- **Increased tokens**: 2048 max output (vs 1024) for detailed rationales
- **Complex tasks**: Optimized for multi-image comparison and structured evaluation
- **Quality over speed**: Prioritizes accuracy for scoring critical appearance attributes

## Model Comparison

| Aspect | Gemini 2.5 Flash | Gemini 2.5 Pro |
|--------|------------------|----------------|
| **Speed** | Very Fast | Moderate |
| **Cost** | Lower | Higher |
| **Reasoning** | Good | Excellent ✅ |
| **Context** | Good | Excellent ✅ |
| **Visual Analysis** | Good | Superior ✅ |
| **Best For** | High-volume, simple tasks | Complex analysis, quality-critical tasks |

## For Your Use Case

**Visual Fidelity Scoring Requirements:**
- ✅ Analyze 5+ GT images simultaneously
- ✅ Compare against 1 candidate with detailed attention
- ✅ Evaluate 6 nuanced dimensions (color, materials, textures, etc.)
- ✅ Generate structured JSON with subscores and rationales
- ✅ High accuracy requirement (this is quality assessment)

**Verdict**: **Gemini 2.5 Pro is the right choice** for this complex visual reasoning task.

## Usage

### Default (Recommended)
```powershell
# Uses Gemini 2.5 Pro automatically
vfscore run-all
```

### Explicit Model Selection
```powershell
# Gemini 2.5 Pro (recommended)
vfscore score --model gemini-2.5-pro

# Gemini 2.5 Flash (faster, less accurate)
vfscore score --model gemini-2.5-flash
```

## Cost Implications

### Gemini 2.5 Pro Pricing (as of 2025)
- **Free tier**: Available with generous limits
- **Rate limits**: 2 RPM (requests per minute) on free tier
- **For your 3 items**: 9 requests (3 items × 3 repeats) = ~5 minutes
- **Recommendation**: Free tier is sufficient for small-scale testing

### If Scaling Up
- Consider upgrading to paid tier for:
  - Higher rate limits (10+ RPM)
  - More daily quota
  - Longer context windows
- Alternative: Use Gemini 2.5 Flash for high-volume simple tasks

## Migration Notes

**If you already ran the pipeline with the old model:**

1. **Outputs are still valid** for testing
2. **For production scoring**, re-run with new model:
   ```powershell
   # Clear old scores
   Remove-Item -Recurse outputs\llm_calls\*
   
   # Re-score with Gemini 2.5 Pro
   vfscore score --model gemini-2.5-pro --repeats 3
   vfscore aggregate
   vfscore report
   ```

3. **Compare results** between models if curious:
   - Run both and compare scores
   - Evaluate quality of rationales
   - Check confidence metrics

## Documentation Updated

All documentation now references **Gemini 2.5 Pro**:
- ✅ README.md
- ✅ SETUP.md
- ✅ QUICKSTART.md
- ✅ PROJECT_STATUS.md
- ✅ BUILD_COMPLETE.md

## Testing

Run the setup test to verify:
```powershell
python tests\test_setup.py
```

Should show: `Using model: gemini-2.5-pro`

## Questions?

### Q: Can I still use Gemini 2.5 Flash?
**A**: Yes! Use `--model gemini-2.5-flash` flag. But Gemini 2.5 Pro is recommended for quality.

### Q: Is Gemini 2.5 Pro free?
**A**: Yes, free tier available. Rate limits apply (2 RPM).

### Q: Will this affect my existing results?
**A**: No, existing outputs are preserved. Re-run scoring to update.

### Q: What about Phase 2 multi-model ensemble?
**A**: Phase 2 will add GPT-4V alongside Gemini 2.5 Pro for cross-validation.

---

**Status**: ✅ **Fixed and Ready**

**Next Steps**: Run `vfscore run-all` with the corrected model!
