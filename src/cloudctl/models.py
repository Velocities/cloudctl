"""Pydantic models for cloudctl configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TailscaleTarget(BaseModel):
    """Local service target and Tailscale listen port for serve/funnel."""

    target: str = Field(
        description="Local port or URL, e.g. 8000 or http://localhost:8080"
    )
    listen_port: int | None = Field(
        default=None,
        description="Port on the .ts.net URL, e.g. 8000 for https://host.ts.net:8000",
    )

    @field_validator("target")
    @classmethod
    def strip_target(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("target cannot be empty")
        return cleaned

    @field_validator("listen_port")
    @classmethod
    def validate_listen_port(cls, value: int | None) -> int | None:
        if value is not None and not 1 <= value <= 65535:
            raise ValueError("listen_port must be between 1 and 65535")
        return value

    def model_post_init(self, __context: object) -> None:
        if self.listen_port is None and self.target.isdigit():
            object.__setattr__(self, "listen_port", int(self.target))

    def display_label(self) -> str:
        if self.listen_port is None:
            return self.target
        if self.target == str(self.listen_port):
            return f":{self.listen_port}"
        return f"{self.target} -> :{self.listen_port}"


class ProjectConfig(BaseModel):
    """Docker Compose project and Tailscale port configuration."""

    name: str = Field(description="Human-readable project identifier")
    compose_dir: Path = Field(description="Directory containing docker-compose.yml")
    compose_project: str | None = Field(
        default=None,
        description="Optional docker compose -p project name",
    )
    serve: list[TailscaleTarget] = Field(default_factory=list)
    funnel: list[TailscaleTarget] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("project name cannot be empty")
        return cleaned

    @field_validator("compose_dir", mode="before")
    @classmethod
    def expand_compose_dir(cls, value: str | Path) -> Path:
        return Path(value).expanduser().resolve()

    @field_validator("compose_project")
    @classmethod
    def normalize_compose_project(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class CloudctlConfig(BaseModel):
    """Top-level persisted configuration."""

    projects: dict[str, ProjectConfig] = Field(default_factory=dict)

    def get_project(self, key: str) -> ProjectConfig | None:
        return self.projects.get(key)

    def add_project(self, key: str, project: ProjectConfig) -> None:
        self.projects[key] = project

    def remove_project(self, key: str) -> ProjectConfig | None:
        return self.projects.pop(key, None)

    def list_projects(self) -> list[tuple[str, ProjectConfig]]:
        return sorted(self.projects.items(), key=lambda item: item[0].lower())
