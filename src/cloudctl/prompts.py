"""Interactive prompts for cloudctl."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt

from cloudctl.docker_ops import find_compose_file as locate_compose_file
from cloudctl.models import ProjectConfig, TailscaleTarget

console = Console()


def prompt_project_key(existing: set[str] | None = None) -> str:
    existing = existing or set()
    while True:
        key = Prompt.ask("Project key (used on the CLI)").strip()
        if not key:
            console.print("[red]Project key cannot be empty.[/red]")
            continue
        if key in existing:
            overwrite = Confirm.ask(
                f"Project [bold]{key}[/bold] already exists. Overwrite?",
                default=False,
            )
            if not overwrite:
                continue
        return key


def prompt_compose_dir() -> Path:
    while True:
        raw = Prompt.ask(
            "Compose directory (folder containing docker-compose.yml)",
            default=str(Path.cwd()),
        ).strip()
        compose_dir = Path(raw).expanduser().resolve()
        if not compose_dir.is_dir():
            console.print(f"[red]{compose_dir} is not a directory.[/red]")
            continue
        try:
            locate_compose_file(compose_dir)
        except FileNotFoundError as exc:
            console.print(f"[red]{exc}[/red]")
            continue
        return compose_dir


def prompt_compose_project() -> str | None:
    raw = Prompt.ask(
        "Docker compose project name (-p), optional",
        default="",
    ).strip()
    return raw or None


def parse_tailscale_target(raw: str) -> TailscaleTarget:
    """Parse LOCAL or LOCAL:LISTEN (listen = port on the .ts.net URL)."""
    cleaned = raw.strip()
    if not cleaned:
        raise ValueError("target cannot be empty")

    if "://" not in cleaned and ":" in cleaned:
        local, listen = cleaned.rsplit(":", 1)
        local = local.strip()
        listen = listen.strip()
        if local and listen.isdigit():
            return TailscaleTarget(target=local, listen_port=int(listen))

    return TailscaleTarget(target=cleaned)


def prompt_tailscale_targets(label: str) -> list[TailscaleTarget]:
    console.print(
        f"\n[bold]{label}[/bold] targets for Tailscale "
        "(comma-separated; leave blank for none)"
    )
    console.print(
        "Format: [cyan]LOCAL[/cyan] or [cyan]LOCAL:LISTEN[/cyan] "
        "(LISTEN is the port on your .ts.net URL)"
    )
    console.print(
        "Examples: [dim]8000[/dim] exposes https://your-host.ts.net:8000 -> local :8000; "
        "[dim]8000:8443[/dim] uses :8443 on the URL"
    )
    raw = Prompt.ask("Targets", default="").strip()
    if not raw:
        return []

    targets: list[TailscaleTarget] = []
    for part in raw.split(","):
        cleaned = part.strip()
        if not cleaned:
            continue
        try:
            targets.append(parse_tailscale_target(cleaned))
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
    return targets


def prompt_select_project(
    projects: list[tuple[str, ProjectConfig]],
    *,
    action: str = "start",
) -> tuple[str, ProjectConfig] | None:
    if not projects:
        console.print("[yellow]No projects configured. Run [bold]cloudctl configure[/bold] first.[/yellow]")
        return None

    console.print(f"\n[bold]Select a project to {action}:[/bold]")
    for index, (key, project) in enumerate(projects, start=1):
        compose_project = project.compose_project or "(default)"
        console.print(
            f"  [cyan]{index}.[/cyan] [bold]{key}[/bold] "
            f"— {project.name} ({project.compose_dir}, -p {compose_project})"
        )

    while True:
        choice = Prompt.ask("Enter number or project key").strip()
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(projects):
                return projects[index - 1]
            console.print("[red]Invalid selection.[/red]")
            continue

        matches = [item for item in projects if item[0] == choice]
        if len(matches) == 1:
            return matches[0]
        console.print("[red]Unknown project. Try again.[/red]")


def prompt_tailscale_mode(project: ProjectConfig) -> str | None:
    has_serve = bool(project.serve)
    has_funnel = bool(project.funnel)

    if not has_serve and not has_funnel:
        console.print(
            "[yellow]This project has no Tailscale targets configured; skipping Tailscale setup.[/yellow]"
        )
        return None

    if has_serve and has_funnel:
        while True:
            mode = Prompt.ask(
                "Tailscale mode",
                choices=["serve", "funnel"],
                default="serve",
            )
            return mode

    if has_serve:
        console.print("Only [bold]serve[/bold] targets are configured.")
        if Confirm.ask("Run tailscale serve?", default=True):
            return "serve"
        return None

    console.print("Only [bold]funnel[/bold] targets are configured.")
    if Confirm.ask("Run tailscale funnel?", default=True):
        return "funnel"
    return None


def collect_project_config(name: str) -> ProjectConfig:
    compose_dir = prompt_compose_dir()
    compose_project = prompt_compose_project()
    serve = prompt_tailscale_targets("Serve")
    funnel = prompt_tailscale_targets("Funnel")

    return ProjectConfig(
        name=name,
        compose_dir=compose_dir,
        compose_project=compose_project,
        serve=serve,
        funnel=funnel,
    )
