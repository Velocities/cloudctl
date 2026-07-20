#!/usr/bin/env bash
# Remove cloudctl from ~/.local/bin (does not delete the repo or venv).
set -euo pipefail

LINK="${HOME}/.local/bin/cloudctl"

if [[ -L "${LINK}" ]] || [[ -e "${LINK}" ]]; then
    rm -f "${LINK}"
    echo "Removed ${LINK}"
else
    echo "Nothing to remove at ${LINK}"
fi
