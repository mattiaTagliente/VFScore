# Cost Protection Guide

**CRITICAL**: Read this guide before running `vfscore score` to avoid unexpected charges.

## The Problem

A user received an unexpected €12.77 bill from Google after running the scoring system. This happened because:

1. **Google Gemini API has two modes**:
   - **FREE TIER**: No charges (5 RPM, 100 RPD limits)
   - **PAID TIER**: Charges apply automatically

2. **If billing is enabled in Google Cloud** → You're on PAID TIER (charges apply)

3. **There's NO programmatic way** to detect tier status before making API calls

4. **Solution**: We've implemented a comprehensive cost protection system

---

## Cost Protection System

VFScore now includes **6 layers of protection** to prevent unexpected charges:

### Layer 1: Pre-Flight Billing Warning ⚠️

**When**: Before ANY API calls
**What**: Explicit warning about billing tiers
**Action**: User must confirm API key is on FREE TIER

```
⚠  BILLING WARNING ⚠
================================================================================

The Gemini API has two modes:
  1. FREE TIER: No charges (5 RPM, 100 RPD limits)
  2. PAID TIER: Charges apply ($1.25/M input, $10/M output tokens)

CRITICAL: If you have billing enabled in Google Cloud,
you WILL be charged for API calls!

Do you confirm your API key is on FREE TIER (billing disabled)? [y/N]:
```

**If uncertain**: Answer `N` and check your billing settings first!

### Layer 2: Cost Estimation 💰

**When**: After billing warning, before execution
**What**: Detailed cost breakdown
**Shows**:
- Number of API calls
- Tokens per call
- Cost per call
- Total estimated cost (USD and EUR)

```
================================================================================
Cost Estimate for This Scoring Run
================================================================================

Model                   | Gemini 2.5 Pro
Items to Score          | 52
Repeats per Item        | 3
Total API Calls         | 156

Input Tokens per Call   | 5,000
Output Tokens per Call  | 800
Total Input Tokens      | 780,000
Total Output Tokens     | 124,800

Cost per Call           | $0.0137
TOTAL COST (USD)        | $2.14
TOTAL COST (EUR)        | €1.97

⚠ This will incur charges if billing is enabled!
```

### Layer 3: Pre-Execution Approval ✅

**When**: After seeing cost estimate
**What**: User must explicitly approve
**Action**: Type `y` to proceed, `N` to cancel

```
Do you want to proceed with this scoring run? [y/N]:
```

**If you see a high cost**: Answer `N` and verify your billing settings!

### Layer 4: Real-Time Cost Tracking 📊

**When**: During execution
**What**: Running cost displayed after each item

```
Scoring 558736 (1/52) ━━━━━━━━━━━━ 15% 0:25:00
  558736: 42.3s (3 repeats)
  Running cost: $0.0411
```

You can see costs accumulating in real-time.

### Layer 5: Threshold Alerts 🚨

**When**: Cost exceeds $1, $5, $10, or $20
**What**: Automatic alert + confirmation required

```
⚠  COST THRESHOLD ALERT ⚠
Current cost: $1.02 USD (exceeded $1.00)

Do you want to continue? (Current: $1.02) [y/N]:
```

**You can abort at any time** to prevent further charges!

### Layer 6: Final Cost Summary 📝

**When**: After execution completes
**What**: Complete cost breakdown + permanent log

```
================================================================================
Cost Tracking Summary
================================================================================

Metric             │ Value
───────────────────┼─────────────────
Model              │ Gemini 2.5 Pro
Total Calls        │ 156
Total Cost (USD)   │ $2.1372
Cost per Call (USD)│ $0.0137
Total Input Tokens │ 780,000
Total Output Tokens│ 124,800
================================================================================

⚠ COSTS INCURRED ⚠
Total cost: $2.1372 USD (≈€1.9662 EUR)
Check your Google Cloud billing console for actual charges.

Cost logs saved to outputs/llm_calls/cost_tracker.json
```

---

## How to Ensure FREE TIER

Follow these steps to verify you're on FREE TIER:

### Step 1: Go to Google AI Studio

https://aistudio.google.com/

### Step 2: Check Your Project

1. Click on your project name (top right)
2. Go to "Settings" or "Billing"
3. Look for billing status

### Step 3: Disable Billing (if enabled)

If you see "Billing enabled" or a credit card:

1. Click "Manage billing"
2. **Disable billing** for this project
3. Confirm you're on FREE TIER

### Step 4: Verify Rate Limits

Free tier has:
- **5 requests per minute (RPM)**
- **100 requests per day (RPD)**

If you see higher limits → You're on PAID TIER!

---

## Pricing Reference

### Gemini 2.5 Pro (Paid Tier)

- **Input**: $1.25 per 1 million tokens
- **Output**: $10.00 per 1 million tokens

### Typical VFScore Call

- **Input**: ~5,000 tokens (messages + 4 images)
- **Output**: ~800 tokens (JSON response)
- **Cost per call**: ~$0.0137 USD

### Example Costs

| Items | Repeats | Total Calls | Est. Cost (USD) | Est. Cost (EUR) |
|-------|---------|-------------|-----------------|-----------------|
| 10    | 3       | 30          | $0.41           | €0.38           |
| 52    | 3       | 156         | $2.14           | €1.97           |
| 100   | 5       | 500         | $6.85           | €6.30           |

**Note**: Actual costs may vary based on image sizes and response lengths.

---

## Cost Tracking Logs

All costs are logged to:
```
outputs/llm_calls/cost_tracker.json
```

**Log contents**:
- Timestamp for each call
- Item ID
- Token counts (input/output)
- Cost per call
- Cumulative cost
- Model info

**Example**:
```json
{
  "summary": {
    "model": "Gemini 2.5 Pro",
    "total_calls": 156,
    "total_cost_usd": 2.1372,
    "cost_per_call_usd": 0.0137
  },
  "calls": [
    {
      "timestamp": "2025-10-25T15:30:45Z",
      "item_id": "558736",
      "input_tokens": 5000,
      "output_tokens": 800,
      "cost_usd": 0.0137,
      "cumulative_cost_usd": 0.0137
    },
    ...
  ]
}
```

---

## What If I Get Charged?

If you receive an unexpected charge:

1. **Check your Google Cloud billing console**:
   - Go to https://console.cloud.google.com/billing
   - View detailed usage reports
   - Verify the charges match your expectations

2. **Review cost_tracker.json**:
   - Compare VFScore logs with Google's billing
   - Check number of calls and costs per call

3. **Disable billing immediately**:
   - Prevent further charges
   - Switch to FREE TIER

4. **Contact Google Cloud Support** (if needed):
   - Explain the situation
   - Request refund if charges were unintended

---

## Best Practices

### ✅ DO:
- Always check billing status before running scoring
- Start with small batches (10 items) to test
- Monitor running costs during execution
- Use FREE TIER for development and testing
- Save cost_tracker.json logs for accounting

### ❌ DON'T:
- Skip the billing warning confirmation
- Run large batches without checking costs
- Enable billing unless you explicitly need paid tier
- Ignore threshold alerts
- Delete cost logs before verification

---

## FAQ

**Q: How do I know if I'm on FREE TIER?**
A: Check https://aistudio.google.com/ → Settings → Billing. If billing is disabled and you see 5 RPM / 100 RPD limits, you're on FREE TIER.

**Q: What happens if I exceed FREE TIER limits?**
A: If billing is DISABLED → API calls fail with 429 errors (no charges).
If billing is ENABLED → You get charged at paid tier rates!

**Q: Can VFScore detect my tier status automatically?**
A: No. Google doesn't provide an API to check tier status. That's why we have multi-layer protection with user confirmation.

**Q: What if cost estimate says $0.00?**
A: This means you're likely on FREE TIER or VFScore couldn't estimate costs. Proceed with caution and monitor the running cost display.

**Q: Can I disable cost protection?**
A: No. Cost protection is mandatory to prevent accidental charges. All confirmations are required.

**Q: What if I accidentally started a large scoring run?**
A: Press `Ctrl+C` immediately to stop execution. Cost tracker will save logs for the calls that completed. Check threshold alerts - they give you chances to abort.

---

## Summary

**VFScore now has comprehensive cost protection**:

1. ⚠️ **Billing warning** before any calls
2. 💰 **Cost estimation** before execution
3. ✅ **User approval** required
4. 📊 **Real-time tracking** during execution
5. 🚨 **Threshold alerts** at $1, $5, $10, $20
6. 📝 **Final summary** with permanent logs

**You are protected from unexpected charges** - but you must:
- Verify your billing status
- Read the warnings carefully
- Monitor costs during execution
- Abort if costs are higher than expected

**Stay safe!** 🛡️
