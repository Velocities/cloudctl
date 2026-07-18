"""Pydantic models for cloudctl configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TailscaleTarget(BaseModel):
    """A local service target for tailscale serve or funnel."""

    target: str = Field(
        description="Port number or URL, e.g. 3000 or http://localhost:8080"
    )

    @field_validator("target")
    @classmethod
    def strip_target(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("target cannot be empty")
        return cleaned


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
