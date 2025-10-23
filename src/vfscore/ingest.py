"""Data ingestion: load items from data sources and create manifest."""

import json
from pathlib import Path
from typing import Iterator

from rich.console import Console

from vfscore.config import Config
from vfscore.data_sources import ItemRecord, DataSource, LegacySource, Archi3DSource

console = Console()


def create_data_source(config: Config) -> DataSource:
    """
    Create appropriate data source based on configuration.

    Args:
        config: VFScore configuration

    Returns:
        DataSource instance (LegacySource or Archi3DSource)

    Raises:
        ValueError: If data_source.type is invalid
        FileNotFoundError: If required files are missing
    """
    source_type = config.data_source.type.lower()

    if source_type == "legacy":
        console.print("[bold]Using LegacySource (database.csv)[/bold]")

        # Get base path (required)
        base_path = config.data_source.base_path
        if not base_path:
            raise ValueError(
                "data_source.base_path must be specified for legacy mode. "
                "Add it to config.local.yaml"
            )
        if not base_path.exists():
            raise FileNotFoundError(f"Base path not found: {base_path}")

        # Get database CSV path
        database_csv = config.data_source.database_csv
        if not database_csv or not database_csv.exists():
            raise FileNotFoundError(f"Database CSV not found: {database_csv}")

        # Get dataset folder relative path
        dataset_folder_rel = config.data_source.dataset_folder

        # Get selected objects CSV (optional)
        selected_objects_csv = config.data_source.selected_objects_csv
        if selected_objects_csv and not selected_objects_csv.exists():
            console.print(f"[yellow]Warning:[/yellow] selected_objects_csv not found, ignoring: {selected_objects_csv}")
            selected_objects_csv = None

        return LegacySource(
            database_csv=database_csv,
            base_path=base_path,
            dataset_folder_rel=dataset_folder_rel,
            selected_objects_csv=selected_objects_csv,
        )

    elif source_type == "archi3d":
        console.print("[bold]Using Archi3DSource (tables/generations.csv)[/bold]")

        # Get workspace path
        workspace = config.data_source.workspace
        if not workspace or not workspace.exists():
            raise FileNotFoundError(f"Archi3D workspace not found: {workspace}")

        # Get run_id (optional)
        run_id = config.data_source.run_id

        # Get custom table paths (optional)
        items_csv = config.data_source.items_csv
        generations_csv = config.data_source.generations_csv

        return Archi3DSource(
            workspace=workspace,
            run_id=run_id,
            items_csv=items_csv,
            generations_csv=generations_csv,
        )

    else:
        raise ValueError(
            f"Invalid data_source.type: '{source_type}'. "
            f"Must be 'legacy' or 'archi3d'"
        )


def create_manifest_from_items(items: Iterator[ItemRecord], output_path: Path) -> int:
    """
    Create manifest JSONL file from ItemRecord iterator.

    Args:
        items: Iterator of ItemRecord instances
        output_path: Path to write manifest.jsonl

    Returns:
        Number of records written

    Raises:
        ValueError: If no items provided
    """
    manifest_records = []

    for item in items:
        record = {
            "item_id": item.item_id,
            "product_id": item.product_id,
            "variant": item.variant,
            "ref_paths": [str(p) for p in item.ref_image_paths],
            "glb_path": str(item.glb_path),
            "algorithm": item.algorithm,
            "job_id": item.job_id,
            "n_refs": len(item.ref_image_paths),
            # Metadata
            "product_name": item.product_name or "",
            "manufacturer": item.manufacturer or "",
            "category_l1": item.category_l1 or "unknown",
            "category_l2": item.category_l2 or "unknown",
            "category_l3": item.category_l3 or "unknown",
            "source_type": item.source_type,
        }

        manifest_records.append(record)

    if not manifest_records:
        raise ValueError("No items to write to manifest")

    # Write manifest
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for record in manifest_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    console.print(f"[green]Manifest created with {len(manifest_records)} records[/green]")

    # Print summary
    console.print("\n[bold]Summary by item:[/bold]")

    # Group by (product_id, variant)
    items_by_key = {}
    for record in manifest_records:
        key = (record["product_id"], record["variant"])
        if key not in items_by_key:
            items_by_key[key] = []
        items_by_key[key].append(record)

    console.print(f"  Unique items: {len(items_by_key)}")
    for (product_id, variant), records in sorted(items_by_key.items()):
        variant_str = f" + '{variant}'" if variant else ""
        console.print(f"    {product_id}{variant_str}: {len(records)} generation(s)")

    # Summary by category
    console.print("\n[bold]Summary by category (l3):[/bold]")
    l3_counts = {}
    for record in manifest_records:
        l3 = record["category_l3"]
        l3_counts[l3] = l3_counts.get(l3, 0) + 1

    for l3, count in sorted(l3_counts.items()):
        console.print(f"  {l3}: {count} record(s)")

    # Summary by algorithm
    console.print("\n[bold]Summary by algorithm:[/bold]")
    algo_counts = {}
    for record in manifest_records:
        algo = record["algorithm"]
        algo_counts[algo] = algo_counts.get(algo, 0) + 1

    for algo, count in sorted(algo_counts.items()):
        console.print(f"  {algo}: {count} record(s)")

    return len(manifest_records)


def run_ingest(config: Config) -> Path:
    """
    Run the ingestion process using configured data source.

    Args:
        config: VFScore configuration

    Returns:
        Path to created manifest.jsonl file

    Raises:
        ValueError: If configuration is invalid or no items found
        FileNotFoundError: If required files are missing
    """
    console.print("\n[bold]Loading items from data source...[/bold]")

    # Create data source
    data_source = create_data_source(config)

    # Print source info
    source_info = data_source.get_source_info()
    console.print("\n[bold]Data Source Info:[/bold]")
    for key, value in source_info.items():
        console.print(f"  {key}: {value}")

    # Load items
    console.print(f"\n[bold]Loading items...[/bold]")
    items = data_source.load_items()

    # Create manifest
    manifest_path = config.paths.out_dir / "manifest.jsonl"
    console.print(f"\n[bold]Creating manifest: {manifest_path}[/bold]")

    try:
        num_records = create_manifest_from_items(items, manifest_path)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise

    console.print(f"\n[green]Ingestion complete![/green]")
    return manifest_path


if __name__ == "__main__":
    from vfscore.config import get_config

    config = get_config()
    run_ingest(config)
