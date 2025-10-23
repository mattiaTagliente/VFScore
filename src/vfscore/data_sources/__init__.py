"""
VFScore data sources module.

This module provides a database abstraction layer for VFScore, supporting
multiple data sources:

- LegacySource: Reads from database.csv (validation study data)
- Archi3DSource: Reads from archi3D workspace tables (Phase 6 integration)

All data sources implement the DataSource protocol and yield ItemRecord instances.
"""

from .base import ItemRecord, DataSource
from .legacy_source import LegacySource
from .archi3d_source import Archi3DSource

__all__ = [
    'ItemRecord',
    'DataSource',
    'LegacySource',
    'Archi3DSource',
]
