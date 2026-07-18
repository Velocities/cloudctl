"""Load and save cloudctl YAML configuration."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import ValidationError

from cloudctl.models import CloudctlConfig, ProjectConfig

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "cloudctl"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"


def config_path() -> Path:
    override = os.environ.get("CLOUDCTL_CONFIG")
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_CONFIG_PATH


def ensure_config_dir(path: Path | None = None) -> Path:
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def load_config(path: Path | None = None) -> CloudctlConfig:
    target = path or config_path()
    if not target.exists():
        return CloudctlConfig()

    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    if raw is None:
        return CloudctlConfig()

    try:
        return CloudctlConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration at {target}: {exc}") from exc


def save_config(config: CloudctlConfig, path: Path | None = None) -> Path:
    target = ensure_config_dir(path or config_path())
    payload = config.model_dump(mode="json")
    target.write_text(
        yaml.safe_dump(payload, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return target


def project_to_yaml_preview(project: ProjectConfig) -> str:
    payload = project.model_dump(mode="json")
    return yaml.safe_dump(payload, sort_keys=False, default_flow_style=False)
