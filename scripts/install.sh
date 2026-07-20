#!/usr/bin/env bash
# Install cloudctl onto your user PATH (~/.local/bin).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
BIN_DIR="${HOME}/.local/bin"
LINK="${BIN_DIR}/cloudctl"

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

case ":${PATH}:" in
    *":${BIN_DIR}:"*) ;;
    *)
        echo "Note: ${BIN_DIR} is not on PATH in this shell."
        echo "Add to ~/.profile or ~/.bashrc (Ubuntu often already has this):"
        echo ""
        echo '  export PATH="$HOME/.local/bin:$PATH"'
        echo ""
        ;;
esac

echo "Try: cloudctl version"
"${LINK}" version
