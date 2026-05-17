from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: str | Path = ".env", override: bool = True) -> bool:
    """Load KEY=VALUE pairs from an env file without requiring python-dotenv."""
    env_path = Path(path)
    if not env_path.exists():
        return False

    try:
        from dotenv import load_dotenv

        load_dotenv(env_path, override=override)
        return True
    except ImportError:
        pass

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if override or key not in os.environ:
            os.environ[key] = value
    return True
