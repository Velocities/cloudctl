#!/usr/bin/env bash
# Install cloudctl onto your user PATH (~/.local/bin).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
BIN_DIR="${HOME}/.local/bin"
LINK="${BIN_DIR}/cloudctl"
MARKER_START="# >>> cloudctl install >>>"
MARKER_END="# <<< cloudctl install <<<"

ensure_path_in_shell() {
    local shell_rc="$1"
    if [[ ! -f "${shell_rc}" ]]; then
        return 0
    fi
    if grep -qF "${MARKER_START}" "${shell_rc}" 2>/dev/null; then
        return 0
    fi

    cat >>"${shell_rc}" <<'EOF'

# >>> cloudctl install >>>
# User-local CLI tools (e.g. cloudctl). Interactive shells read this file, not only ~/.profile.
if [ -d "$HOME/.local/bin" ] ; then
    case ":${PATH}:" in
        *":$HOME/.local/bin:"*) ;;
        *) PATH="$HOME/.local/bin:$PATH" ;;
    esac
fi
# <<< cloudctl install <<<
EOF
    echo "Updated ${shell_rc} to include ~/.local/bin on PATH."
}

bootstrap_venv() {
    if [[ -x "${VENV}/bin/python" ]]; then
        return 0
    fi

    echo "Creating virtual environment at ${VENV}..."
    if python3 -m venv "${VENV}" 2>/dev/null; then
        return 0
    fi

    echo "Creating virtual environment without pip (Debian/Ubuntu fallback)..."
    python3 -m venv "${VENV}" --without-pip
    curl -sS https://bootstrap.pypa.io/get-pip.py -o "${ROOT}/.get-pip.py"
    "${VENV}/bin/python" "${ROOT}/.get-pip.py"
    rm -f "${ROOT}/.get-pip.py"
}

echo "Installing cloudctl from ${ROOT}"

bootstrap_venv

"${VENV}/bin/pip" install -q -r "${ROOT}/requirements.txt"
"${VENV}/bin/pip" install -q -e "${ROOT}"

mkdir -p "${BIN_DIR}"
ln -sfn "${VENV}/bin/cloudctl" "${LINK}"
chmod 755 "${LINK}" 2>/dev/null || true

if [[ ! -x "${LINK}" ]]; then
    echo "error: failed to install ${LINK}" >&2
    exit 1
fi

echo ""
echo "Installed: ${LINK} -> ${VENV}/bin/cloudctl"
echo ""

ensure_path_in_shell "${HOME}/.bashrc"
if [[ -f "${HOME}/.zshrc" ]]; then
    ensure_path_in_shell "${HOME}/.zshrc"
fi

echo ""
echo "Open a new terminal, or run:  source ~/.bashrc"
echo ""
echo "Try: cloudctl version"
"${LINK}" version
