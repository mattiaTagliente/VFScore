"""Multi-key pooling with comprehensive quota tracking for Gemini API."""

import asyncio
import os
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import uuid

from rich.console import Console

from vfscore.llm.base import BaseLLMClient

console = Console(legacy_windows=True)


class QuotaExhaustedError(Exception):
    """Raised when all API keys have exhausted their quotas."""
    pass


class KeyQuotaTracker:
    """Track RPM, TPM, and RPD quotas for a single API key."""

    def __init__(
        self,
        key_id: str,
        rpm_limit: int = 5,
        tpm_limit: int = 125000,
        rpd_limit: int = 100,
    ):
        """
        Args:
            key_id: Identifier for this key (e.g., "key_1", "mattia", etc.)
            rpm_limit: Requests per minute limit
            tpm_limit: Tokens per minute limit
            rpd_limit: Requests per day limit
        """
        self.key_id = key_id
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        self.rpd_limit = rpd_limit

        # Sliding window tracking
        self.request_timestamps = deque(maxlen=rpm_limit)  # Last N requests
        self.token_usage = deque()  # (timestamp, token_count) tuples

        # Daily tracking (resets at midnight Pacific Time)
        self.requests_today = 0
        self.last_reset_date = self._get_current_date_pt()

        # Statistics
        self.total_requests = 0
        self.total_tokens = 0
        self.last_request_time = None

    @staticmethod
    def _get_current_date_pt() -> str:
        """Get current date in Pacific Time (YYYY-MM-DD)."""
        # Simplified: use UTC as approximation (proper timezone handling would need pytz)
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _reset_daily_if_needed(self):
        """Reset daily counters if date has changed."""
        current_date = self._get_current_date_pt()
        if current_date != self.last_reset_date:
            self.requests_today = 0
            self.last_reset_date = current_date
            console.print(f"[dim]  [{self.key_id}] Daily quota reset (new day: {current_date})[/dim]")

    def can_make_request(self, estimated_tokens: int = 5000) -> Tuple[bool, Optional[str]]:
        """
        Check if a request can be made without exceeding quotas.

        Args:
            estimated_tokens: Estimated token usage for this request

        Returns:
            (can_proceed, reason_if_blocked)
        """
        self._reset_daily_if_needed()

        now = time.monotonic()

        # Check RPD (daily quota)
        if self.requests_today >= self.rpd_limit:
            return False, f"Daily quota exhausted ({self.requests_today}/{self.rpd_limit})"

        # Check RPM (requests per minute)
        if len(self.request_timestamps) >= self.rpm_limit:
            oldest = self.request_timestamps[0]
            time_since_oldest = now - oldest
            if time_since_oldest < 60:
                wait_time = 60 - time_since_oldest
                return False, f"RPM limit ({self.rpm_limit}/min), retry in {wait_time:.1f}s"

        # Check TPM (tokens per minute)
        # Remove old token entries (older than 60s)
        while self.token_usage and (now - self.token_usage[0][0]) > 60:
            self.token_usage.popleft()

        current_tpm = sum(tokens for _, tokens in self.token_usage)
        if current_tpm + estimated_tokens > self.tpm_limit:
            return False, f"TPM limit ({current_tpm}/{self.tpm_limit})"

        return True, None

    def get_wait_time(self) -> float:
        """Calculate time to wait before next request can be made."""
        if len(self.request_timestamps) < self.rpm_limit:
            return 0.0

        oldest = self.request_timestamps[0]
        time_since_oldest = time.monotonic() - oldest
        if time_since_oldest < 60:
            return 60 - time_since_oldest + 0.5  # 0.5s safety margin

        return 0.0

    def record_request(self, token_count: int = 5000):
        """Record a completed request for quota tracking."""
        now = time.monotonic()

        self.request_timestamps.append(now)
        self.token_usage.append((now, token_count))

        self._reset_daily_if_needed()
        self.requests_today += 1
        self.total_requests += 1
        self.total_tokens += token_count
        self.last_request_time = datetime.now(timezone.utc).isoformat()

    def get_stats(self) -> Dict[str, Any]:
        """Get current quota statistics."""
        self._reset_daily_if_needed()

        now = time.monotonic()

        # Calculate current RPM
        recent_requests = [ts for ts in self.request_timestamps if (now - ts) < 60]
        current_rpm = len(recent_requests)

        # Calculate current TPM
        while self.token_usage and (now - self.token_usage[0][0]) > 60:
            self.token_usage.popleft()
        current_tpm = sum(tokens for _, tokens in self.token_usage)

        return {
            "key_id": self.key_id,
            "rpm": {
                "current": current_rpm,
                "limit": self.rpm_limit,
                "utilization": f"{(current_rpm / self.rpm_limit) * 100:.1f}%",
            },
            "tpm": {
                "current": current_tpm,
                "limit": self.tpm_limit,
                "utilization": f"{(current_tpm / self.tpm_limit) * 100:.1f}%",
            },
            "rpd": {
                "current": self.requests_today,
                "limit": self.rpd_limit,
                "utilization": f"{(self.requests_today / self.rpd_limit) * 100:.1f}%",
            },
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "last_request": self.last_request_time,
        }


class GeminiKeyPool:
    """Pool of API keys with intelligent quota-aware selection."""

    def __init__(
        self,
        api_keys: List[str],
        key_labels: Optional[List[str]] = None,
        rpm_limit: int = 5,
        tpm_limit: int = 125000,
        rpd_limit: int = 100,
    ):
        """
        Args:
            api_keys: List of Gemini API keys from different users
            key_labels: Optional labels for keys (e.g., ["mattia", "colleague1"])
            rpm_limit: Requests per minute per key
            tpm_limit: Tokens per minute per key
            rpd_limit: Requests per day per key
        """
        if not api_keys:
            raise ValueError("At least one API key required")

        self.api_keys = api_keys
        self.key_labels = key_labels or [f"key_{i+1}" for i in range(len(api_keys))]

        if len(self.key_labels) != len(self.api_keys):
            raise ValueError("Number of key_labels must match number of api_keys")

        # Create quota trackers for each key
        self.trackers = {
            label: KeyQuotaTracker(label, rpm_limit, tpm_limit, rpd_limit)
            for label in self.key_labels
        }

        # Lock for thread-safe key selection
        self._lock = asyncio.Lock()

        # Current key index (round-robin)
        self._current_idx = 0

        console.print(f"[cyan]Initialized key pool with {len(api_keys)} keys: {', '.join(self.key_labels)}[/cyan]")

    async def get_available_key(self, estimated_tokens: int = 5000) -> Tuple[str, str]:
        """
        Get an available API key that can handle the request.

        Returns:
            (api_key, key_label)

        Raises:
            QuotaExhaustedError: If all keys are exhausted
        """
        async with self._lock:
            # Try all keys starting from current index (round-robin)
            attempts = 0
            while attempts < len(self.api_keys):
                label = self.key_labels[self._current_idx]
                tracker = self.trackers[label]

                can_proceed, reason = tracker.can_make_request(estimated_tokens)

                if can_proceed:
                    # Found available key
                    api_key = self.api_keys[self._current_idx]
                    # Move to next key for next request (round-robin)
                    self._current_idx = (self._current_idx + 1) % len(self.api_keys)
                    return api_key, label

                # Try next key
                self._current_idx = (self._current_idx + 1) % len(self.api_keys)
                attempts += 1

            # All keys exhausted - calculate minimum wait time
            min_wait = min(tracker.get_wait_time() for tracker in self.trackers.values())

            if min_wait > 0 and min_wait < 120:  # If reasonable wait time (< 2 min)
                console.print(f"[yellow]All keys busy, waiting {min_wait:.1f}s for next available slot...[/yellow]")
                await asyncio.sleep(min_wait)
                # Try again recursively
                return await self.get_available_key(estimated_tokens)

            # All keys exhausted for extended period
            raise QuotaExhaustedError(
                f"All {len(self.api_keys)} API keys have exhausted their quotas. "
                f"Please wait or add more keys. Minimum wait: {min_wait:.1f}s"
            )

    def record_request(self, key_label: str, token_count: int = 5000):
        """Record a completed request for the specified key."""
        if key_label in self.trackers:
            self.trackers[key_label].record_request(token_count)

            # Warn at 80% daily quota
            stats = self.trackers[key_label].get_stats()
            rpd_used = stats["rpd"]["current"]
            rpd_limit = stats["rpd"]["limit"]

            if rpd_used == int(rpd_limit * 0.8):
                console.print(f"[yellow]⚠ [{key_label}] 80% daily quota used ({rpd_used}/{rpd_limit})[/yellow]")

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all keys."""
        return {label: tracker.get_stats() for label, tracker in self.trackers.items()}

    def print_stats(self):
        """Print formatted statistics for all keys."""
        console.print("\n[bold]API Key Pool Statistics[/bold]")
        console.print("=" * 80)

        for label, stats in self.get_all_stats().items():
            console.print(f"\n[cyan]Key: {label}[/cyan]")
            console.print(f"  RPM: {stats['rpm']['current']}/{stats['rpm']['limit']} ({stats['rpm']['utilization']})")
            console.print(f"  TPM: {stats['tpm']['current']}/{stats['tpm']['limit']} ({stats['tpm']['utilization']})")
            console.print(f"  RPD: {stats['rpd']['current']}/{stats['rpd']['limit']} ({stats['rpd']['utilization']})")
            console.print(f"  Total: {stats['total_requests']} requests, {stats['total_tokens']} tokens")
            if stats['last_request']:
                console.print(f"  Last: {stats['last_request']}")

        console.print("=" * 80 + "\n")

    def save_stats(self, output_path: Path):
        """Save statistics to JSON file."""
        stats = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "keys": self.get_all_stats(),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        console.print(f"[dim]Stats saved to {output_path}[/dim]")
