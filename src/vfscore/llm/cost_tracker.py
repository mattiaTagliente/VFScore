"""Cost tracking and protection system for LLM API calls.

CRITICAL: Prevents unexpected billing charges by tracking costs and
requiring user confirmation before exceeding thresholds.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.table import Table

console = Console(legacy_windows=True)


class CostEstimator:
    """Estimate costs for Gemini API calls."""

    # Gemini 2.5 Pro pricing (USD per 1M tokens, prompts <= 200k)
    PRICING = {
        "gemini-2.5-pro": {
            "input": 1.25,   # $1.25 per 1M input tokens
            "output": 10.0,  # $10.00 per 1M output tokens
            "name": "Gemini 2.5 Pro"
        },
        "gemini-2.5-flash": {
            "input": 0.075,  # $0.075 per 1M input tokens
            "output": 0.30,  # $0.30 per 1M output tokens
            "name": "Gemini 2.5 Flash"
        }
    }

    # Token estimates
    TOKENS_PER_IMAGE = 1024  # Approximate tokens per image (1024x1024)
    SYSTEM_MESSAGE_TOKENS = 600  # Approximate system message length
    USER_MESSAGE_TOKENS = 400  # Approximate user message length
    RESPONSE_TOKENS = 800  # Approximate response length (JSON with rationale)

    def __init__(self, model_name: str = "gemini-2.5-pro"):
        """Initialize cost estimator.

        Args:
            model_name: Model name to estimate costs for
        """
        # Normalize model name
        if "flash" in model_name.lower():
            self.pricing_key = "gemini-2.5-flash"
        else:
            self.pricing_key = "gemini-2.5-pro"

        if self.pricing_key not in self.PRICING:
            console.print(f"[yellow]⚠ Unknown model: {model_name}, using Gemini 2.5 Pro pricing[/yellow]")
            self.pricing_key = "gemini-2.5-pro"

        self.pricing = self.PRICING[self.pricing_key]
        self.model_name = model_name

    def estimate_tokens(
        self,
        num_gt_images: int = 3,
        num_candidate_images: int = 1,
    ) -> Tuple[int, int]:
        """Estimate token count for a single API call.

        Args:
            num_gt_images: Number of ground truth images
            num_candidate_images: Number of candidate images (usually 1)

        Returns:
            (input_tokens, output_tokens)
        """
        # Input tokens: system + user messages + all images
        input_tokens = (
            self.SYSTEM_MESSAGE_TOKENS +
            self.USER_MESSAGE_TOKENS +
            (num_gt_images + num_candidate_images) * self.TOKENS_PER_IMAGE
        )

        # Output tokens: JSON response with scores and rationale
        output_tokens = self.RESPONSE_TOKENS

        return input_tokens, output_tokens

    def estimate_cost(
        self,
        num_gt_images: int = 3,
        num_candidate_images: int = 1,
    ) -> Tuple[float, Dict[str, float]]:
        """Estimate cost for a single API call.

        Args:
            num_gt_images: Number of ground truth images
            num_candidate_images: Number of candidate images

        Returns:
            (total_cost_usd, breakdown_dict)
        """
        input_tokens, output_tokens = self.estimate_tokens(num_gt_images, num_candidate_images)

        # Calculate costs (pricing is per 1M tokens)
        input_cost = (input_tokens / 1_000_000) * self.pricing["input"]
        output_cost = (output_tokens / 1_000_000) * self.pricing["output"]
        total_cost = input_cost + output_cost

        breakdown = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "total_cost_usd": total_cost,
            "model": self.pricing["name"]
        }

        return total_cost, breakdown

    def estimate_batch_cost(
        self,
        num_items: int,
        repeats_per_item: int,
        num_gt_images: int = 3,
    ) -> Tuple[float, Dict[str, float]]:
        """Estimate total cost for a batch of scoring calls.

        Args:
            num_items: Number of items to score
            repeats_per_item: Number of repeats per item
            num_gt_images: Average number of GT images per item

        Returns:
            (total_cost_usd, breakdown_dict)
        """
        single_cost, single_breakdown = self.estimate_cost(num_gt_images, 1)

        total_calls = num_items * repeats_per_item
        total_cost = single_cost * total_calls

        breakdown = {
            "model": self.pricing["name"],
            "num_items": num_items,
            "repeats_per_item": repeats_per_item,
            "total_calls": total_calls,
            "cost_per_call_usd": single_cost,
            "total_cost_usd": total_cost,
            "input_tokens_per_call": single_breakdown["input_tokens"],
            "output_tokens_per_call": single_breakdown["output_tokens"],
            "total_input_tokens": single_breakdown["input_tokens"] * total_calls,
            "total_output_tokens": single_breakdown["output_tokens"] * total_calls,
        }

        return total_cost, breakdown


class CostTracker:
    """Track actual costs during execution."""

    def __init__(self, model_name: str, output_dir: Path):
        """Initialize cost tracker.

        Args:
            model_name: Model name being used
            output_dir: Directory to save cost logs
        """
        self.estimator = CostEstimator(model_name)
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Running totals
        self.total_calls = 0
        self.total_cost_usd = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # Per-call logs
        self.call_logs = []

        # Session info
        self.session_start = datetime.now(timezone.utc).isoformat()

    def record_call(
        self,
        item_id: str,
        num_gt_images: int,
        estimated_tokens: Optional[Tuple[int, int]] = None,
    ):
        """Record a completed API call.

        Args:
            item_id: ID of item that was scored
            num_gt_images: Number of GT images used
            estimated_tokens: Optional (input_tokens, output_tokens) if known
        """
        if estimated_tokens:
            input_tokens, output_tokens = estimated_tokens
        else:
            input_tokens, output_tokens = self.estimator.estimate_tokens(num_gt_images, 1)

        cost, breakdown = self.estimator.estimate_cost(num_gt_images, 1)

        # Update totals
        self.total_calls += 1
        self.total_cost_usd += cost
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        # Log this call
        call_log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "item_id": item_id,
            "num_gt_images": num_gt_images,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "cumulative_cost_usd": self.total_cost_usd,
            "cumulative_calls": self.total_calls,
        }
        self.call_logs.append(call_log)

    def get_summary(self) -> Dict:
        """Get cost tracking summary."""
        return {
            "session_start": self.session_start,
            "model": self.estimator.pricing["name"],
            "total_calls": self.total_calls,
            "total_cost_usd": self.total_cost_usd,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "cost_per_call_usd": self.total_cost_usd / self.total_calls if self.total_calls > 0 else 0,
        }

    def save_logs(self):
        """Save cost logs to JSON file."""
        log_file = self.output_dir / "cost_tracker.json"

        data = {
            "summary": self.get_summary(),
            "calls": self.call_logs,
        }

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        console.print(f"[dim]Cost logs saved to {log_file}[/dim]")

    def check_threshold(self, threshold_usd: float) -> bool:
        """Check if cost threshold has been exceeded.

        Args:
            threshold_usd: Threshold in USD

        Returns:
            True if threshold exceeded, False otherwise
        """
        return self.total_cost_usd >= threshold_usd

    def print_summary(self):
        """Print cost summary to console."""
        summary = self.get_summary()

        table = Table(title="Cost Tracking Summary", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Model", summary["model"])
        table.add_row("Total Calls", str(summary["total_calls"]))
        table.add_row("Total Cost (USD)", f"${summary['total_cost_usd']:.4f}")
        table.add_row("Cost per Call (USD)", f"${summary['cost_per_call_usd']:.4f}")
        table.add_row("Total Input Tokens", f"{summary['total_input_tokens']:,}")
        table.add_row("Total Output Tokens", f"{summary['total_output_tokens']:,}")

        console.print(table)


def display_billing_warning():
    """Display billing warning (non-interactive).

    This is informational only - execution will proceed automatically.
    """
    console.print("\n" + "=" * 80)
    console.print("[bold yellow]⚠  BILLING INFORMATION ⚠[/bold yellow]")
    console.print("=" * 80)
    console.print()
    console.print("[yellow]The Gemini API has two modes:[/yellow]")
    console.print("  1. [green]FREE TIER[/green]: No charges (5 RPM, 100 RPD limits)")
    console.print("  2. [red]PAID TIER[/red]: Charges apply ($1.25/M input, $10/M output tokens)")
    console.print()
    console.print("[bold]CRITICAL: If you have billing enabled in Google Cloud,[/bold]")
    console.print("[bold red]you WILL be charged for API calls![/bold red]")
    console.print()
    console.print("To check your billing status:")
    console.print("  1. Go to: https://aistudio.google.com/")
    console.print("  2. Check if billing is enabled for your project")
    console.print("  3. Disable billing to use FREE TIER only")
    console.print()
    console.print("[dim]VFScore cannot detect billing status programmatically.[/dim]")
    console.print("[dim]Cost tracking and limits are enabled (see config).[/dim]")
    console.print()


def display_cost_estimate(
    num_items: int,
    repeats: int,
    model: str,
    estimated_cost_usd: float,
    breakdown: Dict,
    max_cost_usd: float = None,
) -> bool:
    """Display cost estimate and check against limit (non-interactive).

    Args:
        num_items: Number of items to score
        repeats: Repeats per item
        model: Model name
        estimated_cost_usd: Estimated total cost
        breakdown: Cost breakdown dict
        max_cost_usd: Maximum allowed cost (from config)

    Returns:
        True if within limit, False if exceeds limit
    """
    console.print("\n" + "=" * 80)
    console.print("[bold]Cost Estimate for This Scoring Run[/bold]")
    console.print("=" * 80)
    console.print()

    table = Table(show_header=True)
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Model", breakdown["model"])
    table.add_row("Items to Score", str(num_items))
    table.add_row("Repeats per Item", str(repeats))
    table.add_row("Total API Calls", str(breakdown["total_calls"]))
    table.add_row("", "")
    table.add_row("Input Tokens per Call", f"{breakdown['input_tokens_per_call']:,}")
    table.add_row("Output Tokens per Call", f"{breakdown['output_tokens_per_call']:,}")
    table.add_row("Total Input Tokens", f"{breakdown['total_input_tokens']:,}")
    table.add_row("Total Output Tokens", f"{breakdown['total_output_tokens']:,}")
    table.add_row("", "")
    table.add_row("Cost per Call", f"${breakdown['cost_per_call_usd']:.4f}")
    table.add_row("[bold]TOTAL COST (USD)[/bold]", f"[bold]${estimated_cost_usd:.2f}[/bold]")

    # Approximate EUR conversion (1 USD ≈ 0.92 EUR as of 2025)
    estimated_cost_eur = estimated_cost_usd * 0.92
    table.add_row("[bold]TOTAL COST (EUR)[/bold]", f"[bold]€{estimated_cost_eur:.2f}[/bold]")

    console.print(table)
    console.print()

    # Check against limit
    if max_cost_usd is not None and estimated_cost_usd > max_cost_usd:
        console.print(f"[bold red]❌ COST LIMIT EXCEEDED[/bold red]")
        console.print(f"[red]Estimated cost (${estimated_cost_usd:.2f}) exceeds limit (${max_cost_usd:.2f})[/red]")
        console.print(f"[red]Execution aborted to prevent charges.[/red]")
        console.print()
        console.print("[yellow]To increase limit, set scoring.max_cost_usd in config.local.yaml[/yellow]")
        return False

    if estimated_cost_usd > 0.10:
        console.print("[yellow]⚠ This will incur charges if billing is enabled![/yellow]")
        if max_cost_usd is not None:
            console.print(f"[yellow]Cost limit: ${max_cost_usd:.2f} (from config)[/yellow]")
        else:
            console.print("[yellow]No cost limit set - execution will proceed[/yellow]")
    console.print()

    return True


def check_cost_threshold(
    tracker: CostTracker,
    max_cost_usd: float = None,
    alert_thresholds_usd: List[float] = [1.0, 5.0, 10.0, 20.0],
) -> bool:
    """Check cost thresholds and automatically stop if max exceeded (non-interactive).

    Args:
        tracker: CostTracker instance
        max_cost_usd: Maximum allowed cost (from config)
        alert_thresholds_usd: List of alert thresholds (informational)

    Returns:
        True to continue, False to stop (max cost exceeded)
    """
    # Check max cost limit (hard stop)
    if max_cost_usd is not None and tracker.total_cost_usd >= max_cost_usd:
        if not hasattr(tracker, "_max_cost_exceeded"):
            tracker._max_cost_exceeded = True
            console.print()
            console.print("[bold red]❌ MAXIMUM COST LIMIT REACHED[/bold red]")
            console.print(f"[red]Current cost: ${tracker.total_cost_usd:.2f} USD >= ${max_cost_usd:.2f}[/red]")
            console.print(f"[red]Execution stopped to prevent further charges.[/red]")
            console.print()
        return False

    # Check alert thresholds (informational only)
    for threshold in alert_thresholds_usd:
        if tracker.check_threshold(threshold) and not hasattr(tracker, f"_threshold_{threshold}_passed"):
            # Mark this threshold as passed
            setattr(tracker, f"_threshold_{threshold}_passed", True)

            console.print()
            console.print("[bold yellow]ℹ  COST THRESHOLD ALERT[/bold yellow]")
            console.print(f"[yellow]Current cost: ${tracker.total_cost_usd:.2f} USD (exceeded ${threshold:.2f})[/yellow]")
            if max_cost_usd is not None:
                remaining = max_cost_usd - tracker.total_cost_usd
                console.print(f"[yellow]Remaining before limit: ${remaining:.2f}[/yellow]")
            console.print()

    return True
