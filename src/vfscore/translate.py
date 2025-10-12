"""Translation orchestration: translate scoring results to Italian."""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from rich.console import Console
from rich.progress import track

from vfscore.config import Config
from vfscore.llm.translator import TranslatorClient

console = Console()


def discover_result_files(llm_calls_dir: Path) -> List[Path]:
    """Discover all scoring result files (rep_*.json) across all batches.

    Args:
        llm_calls_dir: Base directory containing LLM call results

    Returns:
        List of paths to rep_*.json files
    """
    result_files = []

    # Traverse directory structure: model/item_id/[batch_*]/rep_*.json
    for model_dir in llm_calls_dir.iterdir():
        if not model_dir.is_dir():
            continue

        for item_dir in model_dir.iterdir():
            if not item_dir.is_dir():
                continue

            # Check for batch structure
            batch_dirs = [d for d in item_dir.iterdir() if d.is_dir() and d.name.startswith("batch_")]

            if batch_dirs:
                # New batch structure
                for batch_dir in batch_dirs:
                    result_files.extend(batch_dir.glob("rep_*.json"))
            else:
                # Legacy structure (no batches)
                result_files.extend(item_dir.glob("rep_*.json"))

    return result_files


def needs_translation(result_file: Path) -> bool:
    """Check if a result file needs translation.

    Args:
        result_file: Path to rep_*.json file

    Returns:
        True if translation is missing or outdated
    """
    # Build translation file path (e.g., rep_1.json -> rep_1_it.json)
    stem = result_file.stem  # e.g., "rep_1"
    translation_file = result_file.parent / f"{stem}_it.json"

    if not translation_file.exists():
        return True

    # Check if original is newer than translation
    if result_file.stat().st_mtime > translation_file.stat().st_mtime:
        return True

    return False


def translate_result_file(
    result_file: Path,
    translator: TranslatorClient,
    force: bool = False,
) -> bool:
    """Translate a single result file to Italian.

    Args:
        result_file: Path to rep_*.json file
        translator: TranslatorClient instance
        force: Force re-translation even if translation exists

    Returns:
        True if translation was performed, False if skipped
    """
    # Check if translation needed
    if not force and not needs_translation(result_file):
        return False

    # Load original result
    try:
        with open(result_file, "r", encoding="utf-8") as f:
            result = json.load(f)
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to load {result_file}: {e}[/yellow]")
        return False

    # Extract rationale
    rationale_en = result.get("rationale", [])

    if not rationale_en:
        console.print(f"[yellow]Warning: No rationale found in {result_file}[/yellow]")
        return False

    # Translate
    try:
        rationale_it = translator.translate_rationale(rationale_en)

        # Create translation record
        translation = {
            "item_id": result.get("item_id", "unknown"),
            "rationale_it": rationale_it,
            "translation_model": translator.model_name,
            "translation_timestamp": datetime.now().isoformat(),
        }

        # Save translation
        stem = result_file.stem  # e.g., "rep_1"
        translation_file = result_file.parent / f"{stem}_it.json"

        with open(translation_file, "w", encoding="utf-8") as f:
            json.dump(translation, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        console.print(f"[red]Error translating {result_file}: {e}[/red]")
        return False


def run_translation(
    config: Config,
    model: str = "gemini-2.5-flash",
    force: bool = False,
) -> None:
    """Run translation for all scoring results.

    Args:
        config: Configuration object
        model: Translation model to use (default: gemini-2.5-flash)
        force: Force re-translation even if translations exist
    """
    # Determine LLM calls directory
    if config.scoring.results_dir:
        llm_calls_dir = Path(config.scoring.results_dir)
        console.print(f"[cyan]Using shared results directory: {llm_calls_dir}[/cyan]")
    else:
        llm_calls_dir = config.paths.out_dir / "llm_calls"

    if not llm_calls_dir.exists():
        raise FileNotFoundError(f"LLM calls directory not found: {llm_calls_dir}")

    # Discover all result files
    result_files = discover_result_files(llm_calls_dir)

    if not result_files:
        console.print("[yellow]No scoring results found. Run 'vfscore score' first.[/yellow]")
        return

    console.print(f"\n[bold]Found {len(result_files)} result files[/bold]")

    # Filter files that need translation
    if force:
        files_to_translate = result_files
        console.print(f"[cyan]Force mode: translating all {len(files_to_translate)} files[/cyan]")
    else:
        files_to_translate = [f for f in result_files if needs_translation(f)]
        console.print(f"[cyan]{len(files_to_translate)} files need translation[/cyan]")

    if not files_to_translate:
        console.print("[green]All results are already translated![/green]")
        return

    # Initialize translator
    console.print(f"[cyan]Initializing translator with {model}...[/cyan]")
    translator = TranslatorClient(model_name=model)

    # Translate each file
    translated_count = 0
    failed_count = 0

    for result_file in track(files_to_translate, description="Translating"):
        success = translate_result_file(result_file, translator, force=force)
        if success:
            translated_count += 1
        else:
            failed_count += 1

    # Print summary
    console.print(f"\n[green]Translation complete:[/green]")
    console.print(f"  Translated: {translated_count}")
    console.print(f"  Failed: {failed_count}")
    console.print(f"  Skipped: {len(result_files) - len(files_to_translate)}")


if __name__ == "__main__":
    from vfscore.config import get_config

    config = get_config()
    run_translation(config)
