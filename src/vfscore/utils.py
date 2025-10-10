"""Utility functions for VFScore."""

import os
from pathlib import Path


def load_env_file(env_path: Path = Path(".env")) -> None:
    """Load environment variables from .env file.
    
    Simple .env loader that reads KEY=VALUE pairs.
    """
    if not env_path.exists():
        return
    
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Parse KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Set environment variable
                os.environ[key] = value


# Auto-load .env on import if in project root
if Path(".env").exists():
    load_env_file()
