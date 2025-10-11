# Fixing gRPC Warnings

## Problem
When running `vfscore score`, you may see warnings like:
```
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
E0000 00:00:1760109895.577940   16104 alts_credentials.cc:93] ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled.
```

## Root Cause
These warnings come from Google's gRPC library. ALTS (Application Layer Transport Security) is Google Cloud's mutual authentication system. When running outside of GCP, the library falls back to standard TLS and logs this warning.

## Solution Applied ✅

Environment variables are now set at the **very beginning** of three files:

### 1. `src/vfscore/__main__.py` (CLI entry point)
```python
import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
```

### 2. `src/vfscore/scoring.py` (Scoring orchestration)
```python
import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
```

### 3. `src/vfscore/llm/gemini.py` (Gemini client)
```python
import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
```

## Why This Works

**Critical**: Environment variables must be set **before** importing Google libraries. By placing them at the top of each module (before any other imports), we ensure they're applied before gRPC initializes.

## Environment Variables Explained

| Variable | Value | Purpose |
|----------|-------|---------|
| `GRPC_VERBOSITY` | `ERROR` | Suppress gRPC info/warning logs |
| `GLOG_minloglevel` | `2` | Suppress Google logging (0=INFO, 1=WARNING, 2=ERROR) |
| `TF_CPP_MIN_LOG_LEVEL` | `3` | Suppress TensorFlow logs if present |

## Testing

After updating, run:
```powershell
vfscore score --model gemini --repeats 1
```

**Expected**: No gRPC warnings should appear. Only:
```
╭──────────────────────────────╮
│ Step 5: LLM Scoring (gemini) │
╰──────────────────────────────╯
Scoring 3 items with gemini (1 repeats each)...
Using model: gemini-2.5-pro
Scoring with gemini ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
✓ Scoring complete using gemini
```

## If Warnings Still Appear

### Option 1: System-wide Environment Variables (Windows)
```powershell
# Set permanently in PowerShell profile
Add-Content $PROFILE "`n`$env:GRPC_VERBOSITY='ERROR'"
Add-Content $PROFILE "`n`$env:GLOG_minloglevel='2'"

# Reload profile
. $PROFILE
```

### Option 2: Session Environment Variables
```powershell
# Set for current PowerShell session
$env:GRPC_VERBOSITY="ERROR"
$env:GLOG_minloglevel="2"
$env:TF_CPP_MIN_LOG_LEVEL="3"

# Then run
vfscore score
```

### Option 3: Python Warnings Filter (Alternative)
If the above doesn't work, you can also filter warnings in Python:

```python
# Add to __main__.py after imports
import warnings
warnings.filterwarnings("ignore", message=".*ALTS.*")
warnings.filterwarnings("ignore", message=".*absl.*")
```

## Why Your Original Attempt Didn't Work

```python
# ❌ INCORRECT (in gemini.py, after imports started)
import google.generativeai as genai  # Already imported!
os.environ["GRPC_VERBosity"] = "ERROR"  # Too late, and typo in name
```

**Issues**:
1. ⚠️ Variables set **after** Google libraries were imported
2. ⚠️ Typo: `GRPC_VERBosity` → should be `GRPC_VERBOSITY` (all caps)
3. ⚠️ Missing `GLOG_minloglevel` variable

## Verification

Check that environment variables are set correctly:

```python
# In Python
import os
print(os.environ.get("GRPC_VERBOSITY"))  # Should print: ERROR
print(os.environ.get("GLOG_minloglevel"))  # Should print: 2
```

## Additional Notes

### Safe to Ignore
- These warnings don't affect functionality
- The API still works correctly with standard TLS
- It's purely cosmetic (but annoying!)

### When Running on GCP
If you deploy this on Google Cloud Platform:
- Warnings won't appear (ALTS is available)
- No environment variables needed
- Automatic mutual TLS authentication

## Summary

✅ **Fixed in 3 files** at the top before imports  
✅ **Correct variable names** (all uppercase)  
✅ **Complete set** of suppression variables  
✅ **Should work** out of the box now  

**If still seeing warnings**: Try Option 1 or 2 above to set system-wide.
