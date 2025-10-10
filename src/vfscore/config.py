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

    models: List[str] = Field(default=["gemini"])
    repeats: int = 3
    rubric_weights: Dict[str, float] = Field(
        default={
            "color_palette": 40,
            "material_finish": 25,
            "texture_identity": 10,
            "texture_scale_placement": 15,
            "shading_response": 5,
            "rendering_artifacts": 5,
        }
    )
    temperature: float = 0.0
    top_p: float = 1.0


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


class Config(BaseModel):
    """Main configuration model."""

    paths: PathsConfig = Field(default_factory=PathsConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)
    preprocess: PreprocessConfig = Field(default_factory=PreprocessConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    sentinels: SentinelsConfig = Field(default_factory=SentinelsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    phase_1_features: Phase1Config = Field(default_factory=Phase1Config)

    @classmethod
    def load(cls, config_path: Path | str = "config.yaml") -> "Config":
        """Load configuration from YAML file."""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

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
