#!/usr/bin/env bash
# Set up the Python virtual environment for this skill.
# Idempotent: safe to run multiple times, instant if already set up

set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${SKILL_ROOT}/.venv"
REQUIREMENTS="${SKILL_ROOT}/scripts/requirements.txt"

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
