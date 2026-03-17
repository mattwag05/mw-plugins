#!/usr/bin/env bash
# Set up Python virtual environment for calendar-organizer plugin
# Idempotent: safe to run multiple times, instant if already set up

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
VENV_DIR="${PLUGIN_ROOT}/.venv"
REQUIREMENTS="${PLUGIN_ROOT}/scripts/requirements.txt"

if [ -d "${VENV_DIR}" ] && [ -f "${VENV_DIR}/bin/python" ]; then
    # Venv exists, check if requirements are satisfied
    if "${VENV_DIR}/bin/pip" freeze 2>/dev/null | grep -q "openpyxl"; then
        echo "Environment ready: ${VENV_DIR}"
        exit 0
    fi
fi

echo "Setting up virtual environment at ${VENV_DIR}..."
python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install --quiet --upgrade pip
"${VENV_DIR}/bin/pip" install --quiet -r "${REQUIREMENTS}"
echo "Environment ready: ${VENV_DIR}"
