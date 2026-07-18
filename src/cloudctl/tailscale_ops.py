"""Tailscale serve and funnel operations."""

from __future__ import annotations

from typing import Literal

from cloudctl.docker_ops import CommandResult, run_command
from cloudctl.models import ProjectConfig

TailscaleMode = Literal["serve", "funnel"]


def reset_tailscale(mode: TailscaleMode) -> CommandResult:
    return run_command(["tailscale", mode, "reset"])


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
        result = run_command(
            ["tailscale", mode, "--bg", target.target],
            check=True,
        )
        results.append(result)
    return results
