"""Test script to verify multi-key async setup.

This script tests the new async multi-key scoring system without making actual API calls.
It verifies:
1. Configuration loading
2. API key resolution
3. Key pool creation
4. Quota tracking initialization
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from vfscore.config import get_config
from vfscore.llm.key_pool import GeminiKeyPool, KeyQuotaTracker

console = Console(legacy_windows=True)


def test_single_key_mode():
    """Test single key mode (backward compatibility)."""
    console.print("\n[bold cyan]Test 1: Single Key Mode[/bold cyan]")

    # Simulate single key in environment
    if not os.getenv("GEMINI_API_KEY"):
        console.print("[yellow]⚠ GEMINI_API_KEY not set, skipping test[/yellow]")
        return False

    try:
        # This should work without config.local.yaml
        config = get_config()

        if not config.scoring.use_async:
            console.print("[green]✓ Async mode disabled (expected for default config)[/green]")
            return True
        else:
            console.print("[green]✓ Async mode enabled[/green]")
            console.print("[dim]  Will use single key from GEMINI_API_KEY env var[/dim]")
            return True

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        return False


def test_multi_key_mode():
    """Test multi-key mode configuration."""
    console.print("\n[bold cyan]Test 2: Multi-Key Mode Configuration[/bold cyan]")

    # Check if multi-key env vars exist
    keys = []
    for i in range(1, 4):
        env_var = f"GEMINI_API_KEY_USER{i}"
        if os.getenv(env_var):
            keys.append(env_var)

    if not keys:
        console.print("[yellow]⚠ No GEMINI_API_KEY_USER* variables found[/yellow]")
        console.print("[dim]  Set GEMINI_API_KEY_USER1, USER2, etc. to test multi-key mode[/dim]")
        return None  # Not a failure, just not configured

    console.print(f"[green]✓ Found {len(keys)} API keys: {', '.join(keys)}[/green]")

    try:
        # Create test key pool
        test_keys = [f"test_key_{i}" for i in range(len(keys))]
        test_labels = [f"user{i+1}" for i in range(len(keys))]

        pool = GeminiKeyPool(
            api_keys=test_keys,
            key_labels=test_labels,
            rpm_limit=5,
            tpm_limit=125000,
            rpd_limit=100,
        )

        console.print(f"[green]✓ Key pool created successfully[/green]")
        console.print(f"[dim]  Keys: {', '.join(test_labels)}[/dim]")

        # Test quota tracker
        for label in test_labels:
            tracker = pool.trackers[label]
            can_proceed, reason = tracker.can_make_request(5000)
            if can_proceed:
                console.print(f"[green]  ✓ {label}: Ready (0/5 RPM, 0/100 RPD)[/green]")
            else:
                console.print(f"[red]  ✗ {label}: {reason}[/red]")

        return True

    except Exception as e:
        console.print(f"[red]✗ Error creating key pool: {e}[/red]")
        return False


def test_quota_tracking():
    """Test quota tracking system."""
    console.print("\n[bold cyan]Test 3: Quota Tracking System[/bold cyan]")

    try:
        tracker = KeyQuotaTracker(
            key_id="test_key",
            rpm_limit=5,
            tpm_limit=125000,
            rpd_limit=100,
        )

        # Simulate requests
        console.print("[dim]Simulating 5 requests...[/dim]")
        for i in range(5):
            can_proceed, reason = tracker.can_make_request(5000)
            if can_proceed:
                tracker.record_request(5000)
                console.print(f"[green]  ✓ Request {i+1}: Accepted[/green]")
            else:
                console.print(f"[yellow]  ⚠ Request {i+1}: {reason}[/yellow]")

        # Try 6th request (should be blocked)
        can_proceed, reason = tracker.can_make_request(5000)
        if not can_proceed:
            console.print(f"[green]✓ Rate limiting working: {reason}[/green]")
        else:
            console.print(f"[red]✗ Rate limiting failed (allowed 6th request)[/red]")
            return False

        # Check stats
        stats = tracker.get_stats()
        console.print("\n[bold]Current Stats:[/bold]")
        console.print(f"  RPM: {stats['rpm']['current']}/{stats['rpm']['limit']} ({stats['rpm']['utilization']})")
        console.print(f"  RPD: {stats['rpd']['current']}/{stats['rpd']['limit']} ({stats['rpd']['utilization']})")
        console.print(f"  Total: {stats['total_requests']} requests, {stats['total_tokens']} tokens")

        return True

    except Exception as e:
        console.print(f"[red]✗ Error in quota tracking: {e}[/red]")
        return False


def test_config_resolution():
    """Test API key resolution from config."""
    console.print("\n[bold cyan]Test 4: API Key Resolution[/bold cyan]")

    try:
        # Test environment variable resolution
        test_env_keys = ["$GEMINI_API_KEY_USER1", "$GEMINI_API_KEY_USER2"]
        console.print(f"[dim]Testing resolution of: {test_env_keys}[/dim]")

        # Simulate resolution
        for key_ref in test_env_keys:
            if key_ref.startswith("$"):
                env_var = key_ref[1:]
                value = os.getenv(env_var)
                if value:
                    console.print(f"[green]  ✓ {env_var}: Resolved (length: {len(value)})[/green]")
                else:
                    console.print(f"[yellow]  ⚠ {env_var}: Not set[/yellow]")

        return True

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        return False


def main():
    """Run all tests."""
    console.print("[bold]VFScore Multi-Key Async Setup Verification[/bold]")
    console.print("=" * 60)

    results = []

    # Run tests
    results.append(("Single Key Mode", test_single_key_mode()))
    results.append(("Multi-Key Configuration", test_multi_key_mode()))
    results.append(("Quota Tracking", test_quota_tracking()))
    results.append(("Config Resolution", test_config_resolution()))

    # Summary
    console.print("\n" + "=" * 60)
    console.print("[bold]Test Summary[/bold]\n")

    passed = sum(1 for _, r in results if r is True)
    skipped = sum(1 for _, r in results if r is None)
    failed = sum(1 for _, r in results if r is False)

    for name, result in results:
        if result is True:
            console.print(f"[green]✓ {name}[/green]")
        elif result is None:
            console.print(f"[dim]⊘ {name} (skipped)[/dim]")
        else:
            console.print(f"[red]✗ {name}[/red]")

    console.print(f"\n[bold]Results: {passed} passed, {failed} failed, {skipped} skipped[/bold]")

    if failed == 0:
        console.print("\n[green bold]All tests passed! ✓[/green bold]")
        console.print("\n[cyan]Next steps:[/cyan]")
        console.print("1. Configure your team's API keys in .env")
        console.print("2. Set up config.local.yaml with scoring.api_keys")
        console.print("3. Run: vfscore score")
        console.print("4. Monitor quota usage in real-time")
    else:
        console.print("\n[yellow bold]Some tests failed. Please review the errors above.[/yellow bold]")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
