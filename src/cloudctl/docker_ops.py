"""Docker Compose operations."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from cloudctl.models import ProjectConfig


@dataclass
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    check: bool = False,
) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    result = CommandResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )
    if check and not result.ok:
        detail = result.stderr or result.stdout or "unknown error"
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n{detail}"
        )
    return result


def find_compose_file(compose_dir: Path) -> Path:
    candidates = [
        compose_dir / "docker-compose.yml",
        compose_dir / "docker-compose.yaml",
        compose_dir / "compose.yml",
        compose_dir / "compose.yaml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    names = ", ".join(path.name for path in candidates)
    raise FileNotFoundError(
        f"No compose file found in {compose_dir}. Expected one of: {names}"
    )


def stop_all_containers() -> CommandResult:
    listing = run_command(["docker", "ps", "-q"])
    if not listing.stdout:
        return CommandResult(["docker", "stop"], 0, "No running containers.", "")

    container_ids = listing.stdout.splitlines()
    return run_command(["docker", "stop", *container_ids])


def compose_up(project: ProjectConfig) -> CommandResult:
    compose_file = find_compose_file(project.compose_dir)
    command = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
    ]
    if project.compose_project:
        command.extend(["-p", project.compose_project])
    command.extend(["up", "-d"])
    return run_command(command, cwd=project.compose_dir, check=True)


def format_command(command: list[str]) -> str:
    return " ".join(command)
