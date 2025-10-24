"""VFScore CLI - Main entry point for the Visual Fidelity Scoring system."""

# Suppress gRPC/Google library warnings before any imports
import os
os.environ["GRPC_VERBOSITY"] = "NONE"  # Must be NONE, not ERROR
os.environ["GRPC_TRACE"] = ""  # Disable all tracing
os.environ["GRPC_PYTHON_LOG_LEVEL"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GOOGLE_LOGGING_VERBOSITY"] = "3"

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from vfscore import __version__
from vfscore.config import get_config
from vfscore.utils import load_env_file

# Auto-load .env file on startup
load_env_file()

app = typer.Typer(
    name="vfscore",
    help="Visual Fidelity Scoring for 3D Generated Objects",
    add_completion=False,
)
# Use legacy_windows=True for Windows compatibility with Unicode characters
console = Console(legacy_windows=True)


def sanitize_error(e: Exception) -> str:
    """Sanitize exception message for Windows compatibility (remove emojis)."""
    return str(e).encode('ascii', errors='ignore').decode('ascii')


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]VFScore[/bold blue] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """VFScore - Automated Visual Fidelity Scoring for 3D Generated Objects."""
    pass


@app.command()
def ingest(
    config_path: Path = typer.Option("config.yaml", help="Path to config file"),
) -> None:
    """
    Ingest dataset: scan folders and create manifest.
    
    Reads:
    - datasets/refs/<item_id>/*.jpg|png
    - datasets/gens/<item_id>/*.glb
    - metadata/categories.csv
    
    Creates:
    - outputs/manifest.jsonl
    """
    from vfscore.ingest import run_ingest
    
    console.print(Panel.fit("[bold cyan]Step 1: Data Ingestion[/bold cyan]"))
    config = get_config()
    
    try:
        manifest_path = run_ingest(config)
        console.print(f"[green][OK][/green] Manifest created: {manifest_path}")
    except Exception as e:
        console.print(f"[red][ERROR][/red] Ingestion failed: {sanitize_error(e)}")
        raise typer.Exit(code=1)


@app.command()
def preprocess_gt(
    config_path: Path = typer.Option("config.yaml", help="Path to config file"),
) -> None:
    """
    Preprocess ground truth photos: segment, standardize, label.
    
    Reads:
    - datasets/refs/<item_id>/*.jpg|png
    
    Creates:
    - outputs/preprocess/refs/<item_id>/gt_*.png
    """
    from vfscore.preprocess_gt import run_preprocess_gt
    
    console.print(Panel.fit("[bold cyan]Step 2: Ground Truth Preprocessing[/bold cyan]"))
    config = get_config()
    
    try:
        run_preprocess_gt(config)
        console.print("[green][OK][/green] Ground truth images preprocessed")
    except Exception as e:
        console.print(f"[red][ERROR][/red] GT preprocessing failed: {sanitize_error(e)}")
        raise typer.Exit(code=1)


@app.command()
def render_cand(
    config_path: Path = typer.Option("config.yaml", help="Path to config file"),
    fast: bool = typer.Option(False, help="Fast mode: 128 samples instead of 256"),
) -> None:
    """
    Render candidate 3D objects using Blender Cycles.
    
    Reads:
    - datasets/gens/<item_id>/*.glb
    
    Creates:
    - outputs/preprocess/cand/<item_id>/candidate.png
    """
    from vfscore.render_cycles import run_render_candidates
    
    console.print(Panel.fit("[bold cyan]Step 3: Candidate Rendering (Blender Cycles)[/bold cyan]"))
    config = get_config()
    
    if fast:
        console.print("[yellow]Fast mode enabled: 128 samples[/yellow]")
        config.render.samples = 128
    
    try:
        run_render_candidates(config)
        console.print("[green][OK][/green] Candidates rendered")
    except Exception as e:
        console.print(f"[red][ERROR][/red] Rendering failed: {sanitize_error(e)}")
        raise typer.Exit(code=1)


@app.command()
def package(
    config_path: Path = typer.Option("config.yaml", help="Path to config file"),
) -> None:
    """
    Package scoring units: combine GT and candidate images with labels.
    
    Reads:
    - outputs/preprocess/refs/<item_id>/gt_*.png
    - outputs/preprocess/cand/<item_id>/candidate.png
    
    Creates:
    - outputs/labels/<item_id>/gt_*_labeled.png
    - outputs/labels/<item_id>/candidate_labeled.png
    - outputs/labels/<item_id>/packet.json
    """
    from vfscore.packetize import run_packetize
    
    console.print(Panel.fit("[bold cyan]Step 4: Packaging Scoring Units[/bold cyan]"))
    config = get_config()
    
    try:
        run_packetize(config)
        console.print("[green][OK][/green] Scoring packets created")
    except Exception as e:
        console.print(f"[red][ERROR][/red] Packaging failed: {sanitize_error(e)}")
        raise typer.Exit(code=1)


@app.command()
def score(
    model: str = typer.Option("gemini-2.5-pro", help="LLM model: gemini-2.5-pro, gemini-2.5-flash"),
    repeats: int = typer.Option(3, help="Number of repeats per item"),
    temperature: float = typer.Option(None, help="Sampling temperature (overrides config if provided)"),
    top_p: float = typer.Option(None, help="Top-p sampling parameter (overrides config if provided)"),
    config_path: Path = typer.Option("config.yaml", help="Path to config file"),
) -> None:
    """
    Score visual fidelity using LLM vision models.

    Uses Gemini 2.5 Pro by default for complex visual reasoning.

    Reads:
    - outputs/labels/<item_id>/packet.json

    Creates:
    - outputs/llm_calls/<model>/<item_id>/rep_{1,2,3}.json
    """
    from vfscore.scoring import run_scoring

    console.print(Panel.fit(f"[bold cyan]Step 5: LLM Scoring ({model})[/bold cyan]"))
    config = get_config()

    try:
        run_scoring(
            config,
            model=model,
            repeats=repeats,
            temperature=temperature,
            top_p=top_p
        )
        console.print(f"[green][OK][/green] Scoring complete using {model}")
    except Exception as e:
        console.print(f"[red][ERROR][/red] Scoring failed: {sanitize_error(e)}")
        raise typer.Exit(code=1)


@app.command()
def aggregate(
    config_path: Path = typer.Option("config.yaml", help="Path to config file"),
    latest_only: bool = typer.Option(False, "--latest-only", help="Use only the latest batch per item (default: use all batches)"),
    batch_pattern: Optional[str] = typer.Option(None, "--batch-pattern", help="Filter batches containing this string in their name"),
    after_date: Optional[str] = typer.Option(None, "--after", help="Filter batches after this date (YYYY-MM-DD format)"),
) -> None:
    """
    Aggregate scores: compute medians and confidence metrics.

    By default, aggregates across ALL batches for better statistical assessment.
    Use --latest-only to aggregate only the most recent batch per item.

    Reads:
    - outputs/llm_calls/<model>/<item_id>/batch_*/rep_*.json
    - outputs/llm_calls/<model>/<item_id>/batch_*/batch_info.json

    Creates:
    - outputs/results/per_item.jsonl
    - outputs/results/per_item.csv
    """
    from vfscore.aggregate import run_aggregation

    console.print(Panel.fit("[bold cyan]Step 6: Score Aggregation[/bold cyan]"))
    config = get_config()

    try:
        run_aggregation(
            config,
            latest_only=latest_only,
            batch_pattern=batch_pattern,
            after_date=after_date,
        )
        console.print("[green][OK][/green] Scores aggregated")
    except Exception as e:
        console.print(f"[red][ERROR][/red] Aggregation failed: {sanitize_error(e)}")
        raise typer.Exit(code=1)


@app.command()
def translate(
    model: str = typer.Option("gemini-2.5-flash", help="Translation model (default: gemini-2.5-flash)"),
    force: bool = typer.Option(False, "--force", help="Force re-translation even if translations exist"),
    config_path: Path = typer.Option("config.yaml", help="Path to config file"),
) -> None:
    """
    Translate LLM rationales from English to Italian.

    Uses Gemini 2.5 Flash for fast and cost-effective translation.
    Translations are cached to avoid re-translating.

    Reads:
    - outputs/llm_calls/<model>/<item_id>/batch_*/rep_*.json

    Creates:
    - outputs/llm_calls/<model>/<item_id>/batch_*/rep_*_it.json
    """
    from vfscore.translate import run_translation

    console.print(Panel.fit("[bold cyan]Step 6.5: Translation (English → Italian)[/bold cyan]"))
    config = get_config()

    # Check if translation is enabled
    if not config.translation.enabled:
        console.print("[yellow]Translation is disabled in config. Skipping...[/yellow]")
        return

    try:
        run_translation(config, model=model, force=force)
        console.print(f"[green][OK][/green] Translation complete using {model}")
    except Exception as e:
        console.print(f"[red][ERROR][/red] Translation failed: {sanitize_error(e)}")
        raise typer.Exit(code=1)


@app.command()
def report(
    config_path: Path = typer.Option("config.yaml", help="Path to config file"),
) -> None:
    """
    Generate HTML report with thumbnails and scores.
    
    Reads:
    - outputs/results/per_item.jsonl
    - outputs/labels/<item_id>/*.png
    
    Creates:
    - outputs/report/index.html
    """
    from vfscore.report import run_report
    
    console.print(Panel.fit("[bold cyan]Step 7: Report Generation[/bold cyan]"))
    config = get_config()
    
    try:
        report_path = run_report(config)
        console.print(f"[green][OK][/green] Report generated: {report_path}")
    except Exception as e:
        console.print(f"[red][ERROR][/red] Report generation failed: {sanitize_error(e)}")
        raise typer.Exit(code=1)


@app.command()
def run_all(
    model: str = typer.Option("gemini-2.5-pro", help="LLM model to use"),
    repeats: int = typer.Option(3, help="Number of repeats per item"),
    fast: bool = typer.Option(False, help="Fast rendering mode"),
    skip_translation: bool = typer.Option(False, "--skip-translation", help="Skip translation step"),
    config_path: Path = typer.Option("config.yaml", help="Path to config file"),
) -> None:
    """
    Run the complete pipeline: ingest → preprocess → render → score → translate → report.

    Uses Gemini 2.5 Pro by default for best visual reasoning quality.
    Automatically translates results to Italian (can be skipped with --skip-translation).
    """
    console.print(Panel.fit("[bold magenta]VFScore Complete Pipeline[/bold magenta]"))
    console.print(f"[cyan]Model: {model}[/cyan]")
    console.print(f"[cyan]Repeats: {repeats}[/cyan]")
    if fast:
        console.print("[yellow]Fast rendering mode enabled[/yellow]")

    # Run all steps in sequence
    steps = [
        ("ingest", lambda: ingest(config_path)),
        ("preprocess-gt", lambda: preprocess_gt(config_path)),
        ("render-cand", lambda: render_cand(config_path, fast)),
        ("package", lambda: package(config_path)),
        ("score", lambda: score(model, repeats, config_path)),
        ("aggregate", lambda: aggregate(config_path)),
    ]

    # Add translation step if not skipped
    if not skip_translation:
        steps.append(("translate", lambda: translate(config_path=config_path)))

    # Always end with report
    steps.append(("report", lambda: report(config_path)))

    for step_name, step_func in steps:
        try:
            step_func()
        except Exception as e:
            console.print(f"[red]Pipeline stopped at: {step_name}[/red]")
            raise typer.Exit(code=1)

    console.print("\n[bold green][OK] Pipeline complete![/bold green]")


if __name__ == "__main__":
    app()
