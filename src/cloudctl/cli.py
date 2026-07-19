"""Typer CLI entrypoint for cloudctl."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from cloudctl import __version__
from cloudctl.config import config_path, load_config, save_config
from cloudctl.docker_ops import compose_up, format_command, stop_all_containers
from cloudctl.models import CloudctlConfig
from cloudctl.prompts import (
    collect_project_config,
    prompt_project_key,
    prompt_select_project,
    prompt_tailscale_mode,
)
from cloudctl.tailscale_ops import apply_tailscale_mode, tailscale_status

app = typer.Typer(
    name="cloudctl",
    help="Manage Docker Compose projects and Tailscale serve/funnel workflows.",
    no_args_is_help=True,
)
console = Console()


def _load_or_exit() -> CloudctlConfig:
    try:
        return load_config()
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc


@app.callback()
def main_callback() -> None:
    """cloudctl manages local Docker projects outside your git repos."""


@app.command("configure")
def configure_cmd() -> None:
    """Add or update a project configuration interactively."""
    config = _load_or_exit()
    console.print(
        Panel.fit(
            "[bold]Configure a Docker project[/bold]\n"
            "Settings are stored in "
            f"[cyan]{config_path()}[/cyan]",
            title="cloudctl configure",
        )
    )

    key = prompt_project_key(set(config.projects.keys()))
    display_name = typer.prompt("Project display name").strip()
    if not display_name:
        console.print("[red]Project name cannot be empty.[/red]")
        raise typer.Exit(code=1)

    project = collect_project_config(display_name)
    config.add_project(key, project)
    saved_to = save_config(config)

    console.print(
        f"\n[green]Saved project[/green] [bold]{key}[/bold] to [cyan]{saved_to}[/cyan]"
    )


@app.command("start")
def start_cmd() -> None:
    """Stop all containers, start one project, then configure Tailscale."""
    config = _load_or_exit()
    selection = prompt_select_project(config.list_projects(), action="start")
    if selection is None:
        raise typer.Exit(code=1)

    key, project = selection
    console.print(f"\n[bold]Starting project[/bold] [cyan]{key}[/cyan] ({project.name})")

    with console.status("[bold yellow]Stopping all running containers..."):
        stop_result = stop_all_containers()
    if stop_result.ok:
        message = stop_result.stdout or "Done."
        console.print(f"[green]Stopped containers:[/green] {message}")
    else:
        console.print(f"[red]Failed to stop containers:[/red] {stop_result.stderr}")
        raise typer.Exit(code=1)

    with console.status("[bold yellow]Starting docker compose project..."):
        try:
            up_result = compose_up(project)
        except FileNotFoundError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc
        except RuntimeError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc

    console.print(
        f"[green]Compose started:[/green] {format_command(up_result.command)}"
    )
    if up_result.stdout:
        console.print(up_result.stdout)

    mode = prompt_tailscale_mode(project)
    if mode is None:
        console.print("[yellow]Tailscale setup skipped.[/yellow]")
        raise typer.Exit(code=0)

    with console.status(f"[bold yellow]Applying tailscale {mode}..."):
        try:
            tailscale_results = apply_tailscale_mode(project, mode)
        except ValueError as exc:
            console.print(f"[yellow]{exc}[/yellow]")
            raise typer.Exit(code=0) from exc
        except RuntimeError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc

    for result in tailscale_results[1:]:
        console.print(
            f"[green]Tailscale {mode}:[/green] {format_command(result.command)}"
        )

    status = tailscale_status(mode)
    if status.stdout:
        console.print(f"\n[bold]Tailscale URLs[/bold]\n{status.stdout}")

    console.print(f"\n[bold green]Project {key} is running.[/bold green]")


@app.command("list")
def list_cmd() -> None:
    """List configured projects."""
    config = _load_or_exit()
    projects = config.list_projects()

    if not projects:
        console.print(
            "[yellow]No projects configured. Run [bold]cloudctl configure[/bold].[/yellow]"
        )
        raise typer.Exit(code=0)

    table = Table(title="Configured Projects")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Compose Dir")
    table.add_column("-p")
    table.add_column("Serve")
    table.add_column("Funnel")

    for key, project in projects:
        serve = ", ".join(t.display_label() for t in project.serve) or "-"
        funnel = ", ".join(t.display_label() for t in project.funnel) or "-"
        table.add_row(
            key,
            project.name,
            str(project.compose_dir),
            project.compose_project or "-",
            serve,
            funnel,
        )

    console.print(table)
    console.print(f"\nConfig file: [cyan]{config_path()}[/cyan]")


@app.command("remove")
def remove_cmd(
    project_key: str | None = typer.Argument(
        None,
        help="Project key to remove; prompts if omitted.",
    ),
) -> None:
    """Remove a project from configuration."""
    config = _load_or_exit()
    projects = config.list_projects()

    if not projects:
        console.print("[yellow]No projects configured.[/yellow]")
        raise typer.Exit(code=0)

    if project_key:
        if project_key not in config.projects:
            console.print(f"[red]Unknown project key:[/red] {project_key}")
            raise typer.Exit(code=1)
        key = project_key
    else:
        selection = prompt_select_project(projects, action="remove")
        if selection is None:
            raise typer.Exit(code=1)
        key, _ = selection

    if not Confirm.ask(f"Remove project [bold]{key}[/bold]?", default=False):
        console.print("[yellow]Cancelled.[/yellow]")
        raise typer.Exit(code=0)

    removed = config.remove_project(key)
    if removed is None:
        console.print(f"[red]Unknown project key:[/red] {key}")
        raise typer.Exit(code=1)
    save_config(config)
    console.print(f"[green]Removed project[/green] [bold]{key}[/bold] ({removed.name})")


@app.command("version")
def version_cmd() -> None:
    """Show cloudctl version."""
    console.print(f"cloudctl {__version__}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
