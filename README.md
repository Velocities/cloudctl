# cloudctl

Manage Docker Compose projects and Tailscale `serve` / `funnel` from a single CLI, with configuration stored outside your git repos.

## Why

When you switch branches constantly, editing `docker-compose.yml` in each repo is painful. `cloudctl` keeps project metadata (compose directory, `-p` name, Tailscale ports) in a persistent config file so you can stop everything, start one project, and expose it over Tailscale with one command.

## Install (system-wide for your user)

Run once from this repo. It creates/updates the project venv and links `cloudctl` into `~/.local/bin` (same pattern as many user-installed CLI tools on Ubuntu):

```bash
cd ~/cloudctl
chmod +x scripts/install.sh
./scripts/install.sh
```

Open a new terminal (or `source ~/.profile`), then use `cloudctl` from any directory—no `cd`, no `source .venv/bin/activate`.

To remove the command from your PATH (keeps the repo and venv):

```bash
./scripts/uninstall.sh
```

## Developer setup (optional)

If you prefer working inside the venv directly:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

If `python3 -m venv` fails on Debian/Ubuntu (missing `ensurepip`), `scripts/install.sh` handles the `--without-pip` fallback automatically.

## Usage

```bash
cloudctl configure   # add or update a project (interactive)
cloudctl list        # show configured projects
cloudctl start       # stop all containers, start one project, set up Tailscale
cloudctl down        # compose down + Tailscale reset for one project (prompt)
cloudctl down --all  # stop every configured project
cloudctl remove      # remove a project from config
cloudctl version
```

### Configure a project

`cloudctl configure` asks for:

- **Project key** — short identifier used by `start` / `remove`
- **Display name** — human-readable label
- **Compose directory** — folder containing `docker-compose.yml`
- **Compose project name** — optional `-p` value for Docker Compose
- **Serve targets** — comma-separated `LOCAL` or `LOCAL:LISTEN` entries
- **Funnel targets** — same format for `tailscale funnel --bg`

Use `LOCAL:LISTEN` so each project gets a distinct URL port (e.g. `8000` → `https://your-host.ts.net:8000`). Use `8000:8443` to forward local `:8000` through Tailscale port `:8443`.

Config is saved to `~/.config/cloudctl/config.yaml`. Override with `CLOUDCTL_CONFIG`.

### Start workflow

1. Pick a configured project
2. Stop all running Docker containers
3. Run `docker compose up -d` for that project
4. Choose **serve** or **funnel** (when both are configured)
5. Reset and apply Tailscale for the selected mode

### Down workflow

1. Pick a configured project (or pass a project key), or use `--all`
2. Run `docker compose down` for the project(s)
3. Reset Tailscale **serve** and/or **funnel** when that project has those targets configured
4. With `--all`, every configured project is stopped and both Tailscale serve and funnel are reset on this machine

## Example config

```yaml
projects:
  my-api:
    name: My API
    compose_dir: /home/velocities/work/my-api
    compose_project: my-api
    serve:
      - target: "8080"
        listen_port: 8080
    funnel:
      - target: "3000"
        listen_port: 3000
```

## Requirements

- Python 3.10+
- Docker with Compose v2 (`docker compose`)
- Tailscale CLI (`tailscale`)
