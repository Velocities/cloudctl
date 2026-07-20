"""Tailscale serve and funnel operations."""

from __future__ import annotations

from typing import Literal

from cloudctl.docker_ops import CommandResult, run_command
from cloudctl.models import ProjectConfig, TailscaleTarget

TailscaleMode = Literal["serve", "funnel"]


def reset_tailscale(mode: TailscaleMode) -> CommandResult:
    return run_command(["tailscale", mode, "reset"])


def down_tailscale_for_project(project: ProjectConfig) -> list[CommandResult]:
    """Reset Tailscale modes configured for this project."""
    results: list[CommandResult] = []
    if project.serve:
        results.append(reset_tailscale("serve"))
    if project.funnel:
        results.append(reset_tailscale("funnel"))
    return results


def down_all_tailscale() -> list[CommandResult]:
    """Reset both serve and funnel on this node."""
    return [reset_tailscale("serve"), reset_tailscale("funnel")]


def build_tailscale_command(mode: TailscaleMode, target: TailscaleTarget) -> list[str]:
    if target.listen_port is None:
        raise ValueError(
            f"Tailscale target '{target.target}' needs a listen port. "
            "Use LOCAL:LISTEN in configure (e.g. 8000:8000)."
        )

    return [
        "tailscale",
        mode,
        "--bg",
        "--yes",
        f"--https={target.listen_port}",
        target.target,
    ]


def apply_tailscale_mode(
    project: ProjectConfig,
    mode: TailscaleMode,
) -> list[CommandResult]:
    targets = project.serve if mode == "serve" else project.funnel
    if not targets:
        raise ValueError(
            f"Project '{project.name}' has no tailscale {mode} targets configured."
        )

    results: list[CommandResult] = []
    reset_result = reset_tailscale(mode)
    results.append(reset_result)

    for target in targets:
        command = build_tailscale_command(mode, target)
        result = run_command(command, check=True)
        results.append(result)
    return results


def tailscale_status(mode: TailscaleMode) -> CommandResult:
    return run_command(["tailscale", mode, "status"])
