#!/usr/bin/env bash
# Start the website on http://127.0.0.1:8000 with PHP's built-in server.
# First time: create the database (docs/setup.md), copy .env.example to .env.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v php >/dev/null || { echo "PHP 8.1+ is needed (php -v)"; exit 1; }
php -m | grep -qi pdo_mysql || { echo "The pdo_mysql PHP extension is missing"; exit 1; }
[ -f .env ] || { echo "No .env file: run  cp .env.example .env  and fill in DB_PASSWORD"; exit 1; }
echo "Website: http://127.0.0.1:${PORT:-8000}   (Ctrl+C to stop)"
exec php -S "127.0.0.1:${PORT:-8000}" -t web web/router.php
