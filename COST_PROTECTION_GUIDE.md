# Cost Protection Guide (Headless Mode)

**CRITICAL**: Read this guide before running `vfscore score` to avoid unexpected charges.

**UPDATE**: VFScore now operates in **headless mode** (no interactive prompts) for archi3D integration and automated workflows.

## The Problem

A user received an unexpected €12.77 bill from Google after running the scoring system. This happened because:

1. **Google Gemini API has two modes**:
   - **FREE TIER**: No charges (5 RPM, 100 RPD limits)
   - **PAID TIER**: Charges apply automatically

2. **If billing is enabled in Google Cloud** → You're on PAID TIER (charges apply)

3. **There's NO programmatic way** to detect tier status before making API calls

4. **Solution**: We've implemented a comprehensive cost protection system

---

## Cost Protection System (Headless Mode)

VFScore now includes **7 layers of protection** to prevent unexpected charges **WITHOUT any interactive prompts**:

### Layer 1: Pre-Flight Billing Warning ⚠️ (Non-Interactive)

**When**: Before ANY API calls
**What**: Informational warning about billing tiers
**Action**: Displays info, then continues automatically (no prompt)

```
⚠  BILLING INFORMATION ⚠
================================================================================

The Gemini API has two modes:
  1. FREE TIER: No charges (5 RPM, 100 RPD limits)
  2. PAID TIER: Charges apply ($1.25/M input, $10/M output tokens)

CRITICAL: If you have billing enabled in Google Cloud,
you WILL be charged for API calls!

VFScore cannot detect billing status programmatically.
Cost tracking and limits are enabled (see config).

[Continues automatically - no prompt]
```

**Control**: Set `display_billing_warning: false` in config to skip

### Layer 2: Cost Estimation 💰 (Non-Interactive)

**When**: After billing warning, before execution
**What**: Detailed cost breakdown
**Action**: Displays estimate, then proceeds automatically (no prompt)

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
Cost limit: $20.00 (from config)

[Continues automatically - no prompt]
```

**Control**: Set `display_cost_estimate: false` in config to skip

### Layer 3: Configuration-Based Cost Limit 🛡️ (NEW - Headless)

**When**: Before execution starts
**What**: Automatic cost limit check
**Action**: Auto-aborts if estimated cost > `max_cost_usd`

```yaml
# config.local.yaml
scoring:
  max_cost_usd: 20.0  # Maximum $20 per run (auto-abort if exceeded)
  # null = no limit (not recommended for production)
```

**Behavior**:
- If estimate <= limit: Proceeds automatically
- If estimate > limit: **Aborts immediately** (no prompt)

```
❌ COST LIMIT EXCEEDED
Estimated cost ($25.00) exceeds limit ($20.00)
Execution aborted to prevent charges.

Update config.local.yaml to increase limit if needed.
```

### Layer 4: Real-Time Cost Tracking 📊

**When**: During execution
**What**: Running cost displayed after each item

```
Scoring 558736 (1/52) ━━━━━━━━━━━━ 15% 0:25:00
  558736: 42.3s (3 repeats)
  Running cost: $0.0411
```

You can see costs accumulating in real-time.

### Layer 5: Threshold Alerts 🚨 (Informational Only)

**When**: Cost exceeds $1, $5, $10, or $20
**What**: Automatic informational alert
**Action**: Displays warning, continues automatically (no prompt)

```
ℹ  COST THRESHOLD ALERT
Current cost: $1.02 USD (exceeded $1.00)
Remaining before limit: $18.98

[Continues automatically - no prompt]
```

**Auto-stop**: If `max_cost_usd` is set and actual cost reaches limit, execution stops automatically (no prompt required)

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
A: You can disable warnings/estimates but not the hard limit. Set `max_cost_usd: null` to remove limit (not recommended). Set `display_billing_warning: false` and `display_cost_estimate: false` to hide informational displays.

**Q: What if I accidentally started a large scoring run?**
A: Press `Ctrl+C` immediately to stop execution. Cost tracker will save logs for the calls that completed. Check threshold alerts - they give you chances to abort.

---

## Summary

**VFScore now has comprehensive cost protection (Headless Mode)**:

1. ⚠️ **Billing warning** before any calls (informational, no prompt)
2. 💰 **Cost estimation** before execution (informational, no prompt)
3. 🛡️ **Configuration-based limit** (auto-abort if exceeded)
4. 📊 **Real-time tracking** during execution
5. 🚨 **Threshold alerts** at $1, $5, $10, $20 (informational, no prompt)
6. 🛑 **Automatic stop** when max_cost_usd reached
7. 📝 **Final summary** with permanent logs

**Headless Mode Benefits**:
- ✅ **No interactive prompts** - suitable for archi3D integration
- ✅ **Automated workflows** - can run in scheduled jobs
- ✅ **Config-based safety** - set limits once, run safely
- ✅ **Real-time monitoring** - see costs as they accumulate
- ✅ **Automatic abort** - stops at configured limit

**You are protected from unexpected charges** - but you must:
- Verify your billing status (https://aistudio.google.com/)
- Set appropriate `max_cost_usd` in config.local.yaml
- Review cost estimates before large runs
- Check cost logs after execution

**Stay safe!** 🛡️
