"""Configuration management for VFScore."""

from pathlib import Path
from typing import Any, Dict, List

import yaml
from pydantic import BaseModel, Field


class PathsConfig(BaseModel):
    """File paths configuration."""

    refs_dir: Path = Field(default=Path("datasets/refs"))
    gens_dir: Path = Field(default=Path("datasets/gens"))
    categories: Path = Field(default=Path("metadata/categories.csv"))
    hdri: Path = Field(default=Path("assets/lights.hdr"))
    out_dir: Path = Field(default=Path("outputs"))
    blender_exe: Path = Field(default=Path("C:/Program Files/Blender Foundation/Blender 4.5/blender.exe"))


class CameraConfig(BaseModel):
    """Camera positioning configuration."""

    radius: float = 2.2
    azimuth_deg: float = 45.0
    elevation_deg: float = 35.0


class RenderConfig(BaseModel):
    """Blender rendering configuration."""

    engine: str = "cycles"
    samples: int = 256
    fov_deg: float = 42.0
    camera: CameraConfig = Field(default_factory=CameraConfig)
    object_prez_rot_z_deg: float = 20.0
    filmic: bool = True
    film_transparent: bool = True
    denoiser: str = "OIDN"
    resolution: int = 1024


class PreprocessConfig(BaseModel):
    """Image preprocessing configuration."""

    canvas_px: int = 1024
    bg_rgb: List[int] = Field(default=[0, 0, 0])
    crop_margin_frac: float = 0.05
    feather_px: int = 2
    label_bar_frac: float = 0.06
    segmentation_model: str = "u2net"


class ScoringConfig(BaseModel):
    """LLM scoring configuration."""

    models: List[str] = Field(default=["gemini-2.5-pro"])
    repeats: int = 3
    rubric_weights: Dict[str, float] = Field(
        default={
            "color_palette": 40,
            "material_finish": 25,
            "texture_identity": 15,
            "texture_scale_placement": 20,
        }
    )
    temperature: float = 0.0
    top_p: float = 1.0
    use_batch_mode: bool = True
    results_dir: Path | None = None

    # Multi-key support (NEW)
    api_keys: List[str] | None = None  # List of API keys (reads from env vars if starts with $)
    key_labels: List[str] | None = None  # Optional labels for keys (e.g., ["mattia", "colleague1"])
    use_async: bool = True  # Use async client with multi-key pool
    rpm_limit: int = 5  # Requests per minute per key (free tier)
    tpm_limit: int = 125000  # Tokens per minute per key (free tier)
    rpd_limit: int = 100  # Requests per day per key (free tier)

    # Cost protection (NEW)
    max_cost_usd: float | None = None  # Maximum allowed cost in USD (None = no limit)
    display_billing_warning: bool = True  # Display billing info at startup
    display_cost_estimate: bool = True  # Display cost estimate before execution


class SentinelsConfig(BaseModel):
    """Sentinel trials configuration."""

    enabled: bool = False
    positive_threshold: int = 85
    negative_threshold: int = 25


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    save_prompts: bool = True
    save_timing: bool = True
    save_hashes: bool = True


class Phase1Config(BaseModel):
    """Phase 1 specific features."""

    enabled: bool = True
    skip_sentinels: bool = True
    single_model_only: bool = True
    basic_reporting: bool = True


class TranslationConfig(BaseModel):
    """Translation configuration."""

    enabled: bool = True
    model: str = "gemini-2.5-flash"
    cache_translations: bool = True


class DataSourceConfig(BaseModel):
    """Data source configuration for ingest."""

    type: str = "legacy"  # "legacy" or "archi3d"

    # Legacy source options
    base_path: Path | None = None  # Base directory for all legacy data (e.g., Testing/)
    dataset_folder: str = "dataset"  # Relative to base_path (e.g., "dataset")
    database_csv: Path = Field(default=Path("database.csv"))  # Relative to VFScore root
    selected_objects_csv: Path | None = Field(default=Path("selected_objects_optimized.csv"))

    # Archi3D source options
    workspace: Path | None = None
    run_id: str | None = None
    items_csv: Path | None = None
    generations_csv: Path | None = None


class Config(BaseModel):
    """Main configuration model."""

    paths: PathsConfig = Field(default_factory=PathsConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)
    preprocess: PreprocessConfig = Field(default_factory=PreprocessConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    sentinels: SentinelsConfig = Field(default_factory=SentinelsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    phase_1_features: Phase1Config = Field(default_factory=Phase1Config)
    translation: TranslationConfig = Field(default_factory=TranslationConfig)
    data_source: DataSourceConfig = Field(default_factory=DataSourceConfig)

    @classmethod
    def load(cls, config_path: Path | str = "config.yaml") -> "Config":
        """Load configuration from YAML file with local overrides.
        
        This method loads the base config.yaml and then applies any overrides
        from config.local.yaml if it exists. This allows developers to have
        machine-specific settings without modifying the shared config.
        
        Args:
            config_path: Path to the base configuration file
            
        Returns:
            Config instance with applied overrides
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Load base configuration
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Check for local configuration override
        local_config_path = config_path.parent / "config.local.yaml"
        if local_config_path.exists():
            with open(local_config_path, "r", encoding="utf-8") as f:
                local_data = yaml.safe_load(f)
            
            # Deep merge local config into base config
            if local_data:
                data = _deep_merge(data, local_data)

        return cls(**data)

    def get_project_root(self) -> Path:
        """Get project root directory (parent of config.yaml)."""
        return Path.cwd()

    def resolve_paths(self, project_root: Path | None = None) -> None:
        """Resolve all relative paths to absolute paths."""
        if project_root is None:
            project_root = self.get_project_root()

        # Resolve paths
        for field_name in ["refs_dir", "gens_dir", "categories", "hdri", "out_dir"]:
            path = getattr(self.paths, field_name)
            if not path.is_absolute():
                setattr(self.paths, field_name, project_root / path)

        # Resolve data_source paths (base_path should be absolute, dataset_folder is relative)
        for field_name in ["base_path", "database_csv", "selected_objects_csv",
                          "workspace", "items_csv", "generations_csv"]:
            path = getattr(self.data_source, field_name)
            if path is not None and isinstance(path, Path) and not path.is_absolute():
                setattr(self.data_source, field_name, project_root / path)


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries.
    
    Values in 'override' take precedence over 'base'.
    Nested dictionaries are merged recursively.
    
    Args:
        base: Base dictionary
        override: Override dictionary
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            result[key] = _deep_merge(result[key], value)
        else:
            # Override value
            result[key] = value
    
    return result


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load()
        _config.resolve_paths()
    return _config


def reload_config(config_path: Path | str = "config.yaml") -> Config:
    """Reload configuration from file."""
    global _config
    _config = Config.load(config_path)
    _config.resolve_paths()
    return _config
