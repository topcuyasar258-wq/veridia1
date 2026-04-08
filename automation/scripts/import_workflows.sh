#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOMATION_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

python3 "${SCRIPT_DIR}/build_workflows.py"
docker compose \
  --env-file "${AUTOMATION_DIR}/.env" \
  -f "${AUTOMATION_DIR}/docker-compose.yml" \
  exec -T n8n-main \
  n8n import:workflow --separate --input=/files/workflows
