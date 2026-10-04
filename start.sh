#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail

python backend/manage.py migrate --noinput

exec gunicorn \
  --chdir backend \
  config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers 1 \
  --access-logfile - \
  --error-logfile -