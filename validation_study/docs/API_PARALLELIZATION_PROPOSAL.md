# Gemini API Parallelization Proposal

**Date**: 2025-10-25
**Context**: Validation study requires hundreds of API calls, currently taking hours due to conservative rate limiting

## Executive Summary

VFScore can achieve **2.5-5x speedup** for LLM scoring by:
1. **Immediate**: Reduce interval from 31s to 12s (respect actual 5 RPM limit)
2. **Short-term**: Implement async parallelization with rate limiter
3. **Medium-term**: Support multi-key pooling for collaborative teams

All solutions respect Gemini API free tier limits and Terms of Service.

---

## Current State Analysis

### Rate Limits (Gemini 2.5 Pro Free Tier)

| Metric | Free Tier Limit | Current Implementation | Utilization |
|--------|----------------|------------------------|-------------|
| Requests Per Minute (RPM) | 5 | ~1.9 (31s interval) | **38%** |
| Requests Per Day (RPD) | 100 | Unlimited | Risk of hitting ceiling |
| Tokens Per Minute (TPM) | 125,000 | Not tracked | Low (~5k per call) |

**Source**: [Official Gemini API Documentation](https://ai.google.dev/gemini-api/docs/rate-limits)

### Current Implementation (`src/vfscore/llm/gemini.py`)

```python
# Lines 82-86: Conservative 31s interval
self.min_interval_sec = (
    float(env_min) if env_min else
    (min_interval_sec if min_interval_sec is not None else 31.0)
)
```

**Bottleneck**: Sequential processing in `scoring.py:score_item_with_repeats()`
- Processes items one at a time
- Creates new client for each repeat (good for run_id independence)
- Single-threaded execution

**Example**: 52 items × 3 repeats = 156 calls
- Current time: 156 × 31s = **81 minutes** (1h 21m)
- Optimal time: 156 / 5 RPM = **32 minutes**
- **Potential savings**: 49 minutes (60% reduction)

---

## Solution 1: Immediate - Optimize Interval (5 minutes)

### Change

Update `src/vfscore/llm/gemini.py:85`:

```python
# OLD (too conservative for free tier)
self.min_interval_sec = 31.0

# NEW (respect actual 5 RPM limit)
self.min_interval_sec = 12.0  # 60s / 5 requests = 12s
```

### Impact

- **Speedup**: 2.5x faster (31s → 12s)
- **Risk**: Low (still respects 5 RPM limit with safety margin)
- **Effort**: 1-line change + testing
- **Free tier compliance**: ✅ Yes (5 RPM = 12s minimum)

### Implementation

```bash
# Update gemini.py
# Change line 85: 31.0 → 12.0

# Test with small dataset
vfscore score --model gemini-2.5-pro --repeats 3

# Monitor for 429 errors (quota exceeded)
# If no errors after 10 items, proceed with validation study
```

---

## Solution 2: Short-term - Async Parallelization (4-6 hours)

### Architecture

Implement concurrent request processing with intelligent rate limiting:

```python
import asyncio
from asyncio import Semaphore
from collections import deque
import time

class AsyncGeminiClient(BaseLLMClient):
    """Async Gemini client with rate limiting."""

    # Shared rate limiter across all instances
    _rate_limiter_lock = asyncio.Lock()
    _request_timestamps = deque(maxlen=5)  # Track last 5 requests

    async def _wait_for_rate_limit(self):
        """Ensure we don't exceed 5 RPM."""
        async with self._rate_limiter_lock:
            now = time.monotonic()

            # If we have 5 requests in the queue
            if len(self._request_timestamps) == 5:
                # Check if oldest request was within last 60s
                oldest = self._request_timestamps[0]
                time_since_oldest = now - oldest

                if time_since_oldest < 60:
                    # Need to wait before making next request
                    wait_time = 60 - time_since_oldest + 0.5  # 0.5s safety margin
                    await asyncio.sleep(wait_time)

            # Record this request
            self._request_timestamps.append(time.monotonic())

    async def score_visual_fidelity_async(
        self,
        image_paths: List[Path],
        context: Dict[str, Any],
        rubric_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """Async scoring with rate limiting."""

        # Wait for rate limit clearance
        await self._wait_for_rate_limit()

        # Make API call (use run_in_executor for sync API)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._score_sync,
            image_paths,
            context,
            rubric_weights
        )

        return result

async def score_batch_async(
    packets: List[Dict],
    model_name: str,
    temperature: float,
    top_p: float,
    rubric_weights: Dict[str, float],
    repeats: int,
    output_dir: Path,
    max_concurrent: int = 5,  # Match 5 RPM limit
) -> List[Dict]:
    """Score multiple items concurrently with rate limiting."""

    semaphore = Semaphore(max_concurrent)

    async def score_one_item(packet):
        async with semaphore:
            return await score_item_with_repeats_async(
                packet, model_name, temperature, top_p,
                rubric_weights, repeats, output_dir
            )

    # Create tasks for all items
    tasks = [score_one_item(p) for p in packets]

    # Execute concurrently with progress tracking
    results = []
    for coro in asyncio.as_completed(tasks):
        result = await coro
        results.append(result)
        # Update progress bar here

    return results
```

### Benefits

- **Speedup**: 2-5x (depends on API latency variance)
- **Efficiency**: Better utilization of 5 RPM quota
- **Robustness**: Sliding window rate limiter prevents bursts
- **Scalability**: Easily adjustable for paid tiers (increase `max_concurrent`)

### Risks

- **Complexity**: More complex error handling for async code
- **Daily limit**: May hit 100 RPD ceiling faster (need monitoring)
- **Testing**: Requires thorough testing to ensure rate limiter works correctly

### Implementation Steps

1. Create `src/vfscore/llm/gemini_async.py` with `AsyncGeminiClient`
2. Update `scoring.py` to use async scoring
3. Add `--async` flag to `vfscore score` command
4. Implement sliding window rate limiter
5. Add daily quota tracking (warn at 80 requests)
6. Test with small dataset (10 items)
7. Benchmark against synchronous version

**Estimated effort**: 4-6 hours (implementation + testing)

---

## Solution 3: Medium-term - Multi-Key Pooling (8-12 hours)

### Legitimate Use Cases

**✅ ACCEPTABLE** (complies with ToS):
- Multiple researchers working on same project
- Each researcher has their own Google account + API key
- Collaborative research team pooling resources

**❌ PROHIBITED** (violates ToS):
- Creating multiple fake accounts to bypass limits
- Single user with multiple accounts for rate limit evasion
- Automated account creation

### Architecture

```python
class GeminiKeyPool:
    """Pool of API keys from multiple legitimate users."""

    def __init__(self, api_keys: List[str]):
        """
        Args:
            api_keys: List of API keys from different Google accounts
        """
        if not api_keys:
            raise ValueError("At least one API key required")

        self.keys = api_keys
        self.clients = {}
        self.key_stats = {}  # Track usage per key

        for key in api_keys:
            self.clients[key] = GeminiClient(api_key=key, min_interval_sec=12.0)
            self.key_stats[key] = {
                "requests_today": 0,
                "last_reset": datetime.now().date(),
                "requests_this_minute": deque(maxlen=5)
            }

    def get_available_client(self) -> GeminiClient:
        """Get client from least-used key (round-robin + quota-aware)."""

        now = datetime.now()

        for key in self.keys:
            stats = self.key_stats[key]

            # Reset daily counter if new day
            if stats["last_reset"] != now.date():
                stats["requests_today"] = 0
                stats["last_reset"] = now.date()

            # Check daily quota (use 90 to leave safety margin)
            if stats["requests_today"] >= 90:
                continue

            # Check minute quota
            recent_requests = [
                ts for ts in stats["requests_this_minute"]
                if (now.timestamp() - ts) < 60
            ]

            if len(recent_requests) < 5:
                # This key is available
                return self.clients[key], key

        # All keys exhausted - wait or raise error
        raise QuotaExhaustedError(
            "All API keys have reached their quota limits. "
            "Please wait or add more keys."
        )

    def record_request(self, key: str):
        """Record request for quota tracking."""
        now = datetime.now()
        stats = self.key_stats[key]
        stats["requests_today"] += 1
        stats["requests_this_minute"].append(now.timestamp())
```

### Configuration

```yaml
# config.yaml or config.local.yaml
scoring:
  api_keys:
    - ${GEMINI_API_KEY_USER1}  # Main researcher
    - ${GEMINI_API_KEY_USER2}  # Collaborator 1
    - ${GEMINI_API_KEY_USER3}  # Collaborator 2

  # OR use single key (backward compatible)
  api_key: ${GEMINI_API_KEY}
```

### Benefits

- **Speedup**: Linear with number of keys (2 keys = 2x, 3 keys = 3x)
- **Daily quota**: 100 × N requests per day
- **Legitimate**: Complies with ToS (collaborative research)
- **Flexible**: Degrades gracefully to single key if others unavailable

### Risks

- **Coordination**: Requires team coordination (each member provides key)
- **Quota tracking**: Need robust tracking to avoid exceeding per-key limits
- **Fairness**: Need to ensure balanced usage across keys
- **Security**: API keys must be kept secure (use env vars, not commit to git)

### Implementation Steps

1. Create `src/vfscore/llm/key_pool.py` with `GeminiKeyPool`
2. Update config schema to support multiple API keys
3. Modify `scoring.py` to use key pool
4. Add usage statistics tracking
5. Add `vfscore score --show-key-stats` command
6. Document team setup in GUIDE.md
7. Add security warnings to README.md

**Estimated effort**: 8-12 hours (implementation + testing + documentation)

---

## Recommended Implementation Plan

### UPDATED PLAN: Immediate Implementation (All Phases Combined)

**Requirement**: Team has multiple collaborators with API keys - implement full async + multi-key support immediately

**Goal**: Maximum throughput with comprehensive quota tracking (RPM, TPM, RPD per key)

### Implementation Steps (6-8 hours)

1. ✅ Implement `AsyncGeminiClient` with rate limiting
   - Async API calls with `asyncio`
   - Per-key RPM tracking (5 requests/minute)
   - Per-key TPM tracking (125,000 tokens/minute)
   - Per-key RPD tracking (100 requests/day, resets at midnight PT)

2. ✅ Implement `GeminiKeyPool` for multi-key orchestration
   - Round-robin key selection with quota awareness
   - Automatic key rotation when limits reached
   - Real-time quota monitoring and logging
   - Graceful degradation (skip exhausted keys)

3. ✅ Update configuration schema
   - Support multiple API keys via config
   - Backward compatible with single key
   - Environment variable support

4. ✅ Update `scoring.py` for async execution
   - Replace sequential scoring with async batch processing
   - Maintain skip logic for resume capability
   - Preserve progress tracking and timing

5. ✅ Add comprehensive monitoring
   - Per-key quota statistics
   - Warning alerts at 80% quota
   - Detailed logging for debugging

6. ✅ Testing and validation
   - Test with single key (backward compatibility)
   - Test with multiple keys (throughput)
   - Verify quota tracking accuracy

**Time**: 6-8 hours (same day implementation)

---

## Expected Performance

### Validation Study Example

**Study parameters**:
- 52 items × 3 repeats = 156 API calls
- Current: 31s per call = **81 minutes**

| Solution | Interval | Parallelism | Total Time | Speedup | Daily Limit |
|----------|----------|-------------|------------|---------|-------------|
| Current | 31s | Sequential | 81 min | 1.0x | No risk |
| Phase 1 | 12s | Sequential | 31 min | 2.6x | ⚠️ Moderate |
| Phase 2 | 12s | 5 concurrent | 15-20 min | 4-5x | ⚠️ High |
| Phase 3 | 12s | 5×N concurrent | 10-15 min | 5-8x | ✅ Low (distributed) |

### Daily Quota Risk Assessment

**100 requests per day** is the hard limit for free tier.

| Study Size | Requests | Phase 1 Risk | Phase 2 Risk | Phase 3 Risk (2 keys) |
|------------|----------|--------------|--------------|----------------------|
| Small (20 items × 3) | 60 | ✅ Safe | ✅ Safe | ✅ Safe |
| Medium (52 items × 3) | 156 | ⚠️ 1.6 days | ⚠️ 1.6 days | ✅ 1 day |
| Large (100 items × 5) | 500 | ❌ 5 days | ❌ 5 days | ⚠️ 2.5 days (2 keys) |

**Recommendation**: For validation studies >100 requests, consider:
1. Using multiple legitimate collaborator keys (Phase 3)
2. Splitting study across multiple days
3. Upgrading to paid tier ($7-10/month for higher limits)

---

## Security and Compliance

### API Key Management

**✅ DO**:
- Store API keys in `.env` file (never commit to git)
- Use environment variables for configuration
- Restrict file permissions on `.env` (chmod 600)
- Rotate keys periodically
- Use separate keys for dev/production

**❌ DON'T**:
- Commit API keys to git repositories
- Share API keys in chat messages or emails
- Hardcode keys in source code
- Use same key across multiple public projects

### Terms of Service Compliance

**Acceptable Use** (per Google's ToS):
- Research and educational purposes ✅
- Collaborative team projects ✅
- Multiple researchers with own accounts ✅
- Non-commercial PhD research ✅

**Prohibited Use**:
- Creating multiple accounts to evade rate limits ❌
- Automated account creation ❌
- Selling or sharing API access ❌
- Commercial use without paid tier ❌

---

## Testing Plan

### Test 1: Interval Reduction (Phase 1)

```bash
# Test with small dataset
vfscore score --model gemini-2.5-pro --repeats 3

# Monitor console for:
# - "API call failed" messages (indicates 429 errors)
# - Elapsed time per item
# - Total completion time

# Expected: ~12s per repeat, no 429 errors
```

### Test 2: Async Parallelization (Phase 2)

```bash
# Compare sync vs async
vfscore score --model gemini-2.5-pro --repeats 3 --async false
# Note total time

vfscore score --model gemini-2.5-pro --repeats 3 --async true
# Note total time

# Expected: async should be 2-3x faster
# Monitor: No 429 errors, proper rate limiting
```

### Test 3: Multi-Key Pool (Phase 3)

```bash
# Setup .env with multiple keys
GEMINI_API_KEY_USER1=key1
GEMINI_API_KEY_USER2=key2

# Run with key pool
vfscore score --model gemini-2.5-pro --repeats 3 --use-key-pool

# Check key statistics
vfscore score --show-key-stats

# Expected: Balanced usage across keys
```

---

## Conclusion

**Immediate Action** (Recommended):
- Reduce interval to 12s for 2.5x speedup ✅
- Monitor for 429 errors during testing
- Deploy if stable

**Future Work** (Optional):
- Async parallelization for 4-5x speedup (1 day effort)
- Multi-key pooling for collaborative teams (2 days effort)

**Cost-Benefit Analysis**:
- Phase 1: 30 min work → 50 min saved per 156-call study → **ROI after 1 study**
- Phase 2: 6 hour work → 60 min saved per study → **ROI after 6 studies**
- Phase 3: 12 hour work → Enables large studies (>300 calls) → **ROI for PhD research**

All solutions respect Gemini API free tier limits and Terms of Service.
