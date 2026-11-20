#!/usr/bin/env bash
# 本地运行：自动加载 .env（GitHub Actions 用 Secrets，不读这个文件）
set -euo pipefail
cd "$(dirname "$0")"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

if [[ -x .venv/bin/python ]]; then
  exec .venv/bin/python -m market_report "$@"
fi
exec python3 -m market_report "$@"
