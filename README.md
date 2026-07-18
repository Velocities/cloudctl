# cloudctl

Manage Docker Compose projects and Tailscale `serve` / `funnel` from a single CLI, with configuration stored outside your git repos.

## Why

When you switch branches constantly, editing `docker-compose.yml` in each repo is painful. `cloudctl` keeps project metadata (compose directory, `-p` name, Tailscale ports) in a persistent config file so you can stop everything, start one project, and expose it over Tailscale with one command.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

If `python3 -m venv` fails on Debian/Ubuntu (missing `ensurepip`):

```bash
python3 -m venv .venv --without-pip
curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py
.venv/bin/python get-pip.py && rm get-pip.py
pip install -r requirements.txt && pip install -e .
```

## Usage

```bash
cloudctl configure   # add or update a project (interactive)
cloudctl list        # show configured projects
cloudctl start       # stop all containers, start one project, set up Tailscale
cloudctl remove      # remove a project from config
cloudctl version
```

### Configure a project

`cloudctl configure` asks for:

- **Project key** — short identifier used by `start` / `remove`
- **Display name** — human-readable label
- **Compose directory** — folder containing `docker-compose.yml`
- **Compose project name** — optional `-p` value for Docker Compose
- **Serve targets** — comma-separated ports/URLs for `tailscale serve --bg`
- **Funnel targets** — comma-separated ports/URLs for `tailscale funnel --bg`

Config is saved to `~/.config/cloudctl/config.yaml`. Override with `CLOUDCTL_CONFIG`.

### Start workflow

1. Pick a configured project
2. Stop all running Docker containers
3. Run `docker compose up -d` for that project
4. Choose **serve** or **funnel** (when both are configured)
5. Reset and apply Tailscale for the selected mode

## Example config

```yaml
projects:
  my-api:
    name: My API
    compose_dir: /home/velocities/work/my-api
    compose_project: my-api
    serve:
      - target: "8080"
    funnel:
      - target: "3000"
```

## Requirements

- Python 3.10+
- Docker with Compose v2 (`docker compose`)
- Tailscale CLI (`tailscale`)
