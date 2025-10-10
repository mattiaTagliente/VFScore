"""Test script to verify VFScore installation and configuration."""

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def test_python_version() -> bool:
    """Test Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        console.print("[green]✓[/green] Python version OK:", f"{version.major}.{version.minor}.{version.micro}")
        return True
    else:
        console.print(f"[red]✗[/red] Python version {version.major}.{version.minor} < 3.11")
        return False


def test_imports() -> bool:
    """Test required package imports."""
    packages = [
        "typer",
        "pydantic",
        "yaml",
        "PIL",
        "numpy",
        "cv2",
        "google.generativeai",
        "rembg",
        "tqdm",
        "rich",
        "jinja2",
    ]
    
    all_ok = True
    
    for package in packages:
        try:
            __import__(package)
            console.print(f"[green]✓[/green] {package}")
        except ImportError:
            console.print(f"[red]✗[/red] {package} - not installed")
            all_ok = False
    
    return all_ok


def test_vfscore_package() -> bool:
    """Test vfscore package import."""
    try:
        import vfscore
        from vfscore import __version__
        console.print(f"[green]✓[/green] vfscore package (v{__version__})")
        return True
    except ImportError as e:
        console.print(f"[red]✗[/red] vfscore package: {e}")
        return False


def test_config() -> bool:
    """Test configuration file."""
    config_path = Path("config.yaml")
    
    if not config_path.exists():
        console.print(f"[red]✗[/red] config.yaml not found")
        return False
    
    try:
        from vfscore.config import Config
        config = Config.load(config_path)
        console.print("[green]✓[/green] config.yaml loaded successfully")
        return True
    except Exception as e:
        console.print(f"[red]✗[/red] Error loading config: {e}")
        return False


def test_paths() -> bool:
    """Test required paths exist."""
    paths = {
        "datasets/refs": "Reference photos directory",
        "datasets/gens": "Generated objects directory",
        "metadata/categories.csv": "Categories file",
        "assets/lights.hdr": "HDRI lighting file",
    }
    
    all_ok = True
    
    for path_str, description in paths.items():
        path = Path(path_str)
        if path.exists():
            console.print(f"[green]✓[/green] {description}: {path}")
        else:
            console.print(f"[red]✗[/red] {description}: {path} not found")
            all_ok = False
    
    return all_ok


def test_blender() -> bool:
    """Test Blender executable."""
    from vfscore.config import get_config
    
    config = get_config()
    blender_exe = config.paths.blender_exe
    
    if blender_exe.exists():
        console.print(f"[green]✓[/green] Blender found: {blender_exe}")
        return True
    else:
        console.print(f"[red]✗[/red] Blender not found: {blender_exe}")
        console.print("  Update config.yaml with correct Blender path")
        return False


def test_api_keys() -> bool:
    """Test API keys."""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        console.print(f"[green]✓[/green] GEMINI_API_KEY set: {masked_key}")
        return True
    else:
        console.print("[yellow]⚠[/yellow] GEMINI_API_KEY not set")
        console.print("  Create .env file with your API key")
        return False


def test_dataset() -> bool:
    """Test dataset structure."""
    from vfscore.config import get_config
    
    config = get_config()
    
    # Count items
    refs_items = list(config.paths.refs_dir.glob("*")) if config.paths.refs_dir.exists() else []
    gens_items = list(config.paths.gens_dir.glob("*")) if config.paths.gens_dir.exists() else []
    
    refs_items = [d for d in refs_items if d.is_dir()]
    gens_items = [d for d in gens_items if d.is_dir()]
    
    console.print(f"[cyan]ℹ[/cyan] Found {len(refs_items)} items with reference photos")
    console.print(f"[cyan]ℹ[/cyan] Found {len(gens_items)} items with generated objects")
    
    if len(refs_items) > 0 and len(gens_items) > 0:
        console.print("[green]✓[/green] Dataset structure OK")
        return True
    else:
        console.print("[yellow]⚠[/yellow] Dataset appears empty")
        return False


def main():
    """Run all tests."""
    console.print(Panel.fit("[bold magenta]VFScore Installation Test[/bold magenta]"))
    
    tests = [
        ("Python Version", test_python_version),
        ("Package Imports", test_imports),
        ("VFScore Package", test_vfscore_package),
        ("Configuration", test_config),
        ("Required Paths", test_paths),
        ("Blender Executable", test_blender),
        ("API Keys", test_api_keys),
        ("Dataset Structure", test_dataset),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        console.print(f"\n[bold]{test_name}[/bold]")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")
            results.append((test_name, False))
    
    # Summary
    console.print("\n" + "="*60)
    
    table = Table(title="Test Results Summary")
    table.add_column("Test", style="cyan")
    table.add_column("Status", justify="center")
    
    for test_name, result in results:
        status = "[green]PASS[/green]" if result else "[red]FAIL[/red]"
        table.add_row(test_name, status)
    
    console.print(table)
    
    # Overall result
    all_passed = all(result for _, result in results)
    
    if all_passed:
        console.print("\n[bold green]✓ All tests passed! VFScore is ready to use.[/bold green]")
        console.print("\nRun: [bold cyan]vfscore run-all[/bold cyan] to start the pipeline")
    else:
        console.print("\n[bold yellow]⚠ Some tests failed. Please fix the issues above.[/bold yellow]")
        console.print("\nRefer to SETUP.md for detailed setup instructions")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
