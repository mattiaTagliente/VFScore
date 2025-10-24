"""
Base data model and protocol for VFScore data sources.

This module defines the unified data model (ItemRecord) and the protocol
(DataSource) that all data source implementations must follow.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, List, Iterator

# Import make_item_id for consistent item_id generation
from vfscore.utils import make_item_id


@dataclass
class ItemRecord:
    """
    Unified data record for a single scorable item.

    An item is uniquely identified by (product_id, variant).
    Each item may have multiple generations (different job_id values).

    Attributes:
        product_id: Product identifier (e.g., "335888")
        variant: Variant name (e.g., "Curved backrest" or "")
        item_id: Composite identifier "{product_id}_{variant}" or just product_id if variant is empty
        ref_image_paths: List of reference image paths for this item
        glb_path: Path to generated 3D model (.glb file)
        algorithm: Generation algorithm used (e.g., "hunyuan3d-std", "tripo3d-draft")
        job_id: Unique job identifier for this specific generation

        # Optional metadata
        product_name: Human-readable product name
        manufacturer: Manufacturer name
        category_l1: Level 1 category
        category_l2: Level 2 category
        category_l3: Level 3 category

        source_type: Data source type ("archi3d" or "legacy")
    """
    product_id: str
    variant: str
    item_id: str  # Composite: "{product_id}_{variant}" or just product_id if variant empty
    ref_image_paths: List[Path]
    glb_path: Path | None
    algorithm: str | None
    job_id: str | None

    # Optional metadata
    product_name: str | None = None
    manufacturer: str | None = None
    category_l1: str | None = None
    category_l2: str | None = None
    category_l3: str | None = None

    source_type: str = "unknown"

    def __post_init__(self):
        """Validate the record after initialization."""
        if not self.product_id:
            raise ValueError("product_id cannot be empty")

        # Validate item_id matches expected format (using make_item_id for consistency)
        expected_item_id = make_item_id(self.product_id, self.variant)
        if self.item_id != expected_item_id:
            raise ValueError(
                f"item_id '{self.item_id}' doesn't match expected format '{expected_item_id}'"
            )

        # Validate paths
        if not self.ref_image_paths:
            raise ValueError(f"Item {self.item_id} has no reference images")

        for img_path in self.ref_image_paths:
            if not isinstance(img_path, Path):
                raise TypeError(f"ref_image_paths must contain Path objects, got {type(img_path)}")

        if self.glb_path and not isinstance(self.glb_path, Path):
            raise TypeError(f"glb_path must be a Path object, got {type(self.glb_path)}")


class DataSource(Protocol):
    """
    Protocol defining the interface for VFScore data sources.

    All data source implementations (Archi3DSource, LegacySource) must
    implement these methods to provide a consistent interface.
    """

    def load_items(self) -> Iterator[ItemRecord]:
        """
        Load and yield ItemRecord instances from the data source.

        Yields:
            ItemRecord: Individual item records with all metadata

        Raises:
            FileNotFoundError: If required data files are missing
            ValueError: If data is malformed or invalid
        """
        ...

    def get_source_info(self) -> dict:
        """
        Return metadata about this data source.

        Returns:
            dict: Information about the source (type, version, paths, etc.)
        """
        ...
