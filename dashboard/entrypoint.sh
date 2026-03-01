#!/bin/sh
# Entrypoint: inject the API service URL into nginx config at runtime
# Railway sets API_SERVICE_URL as an environment variable.
# Falls back to proxying /api locally if not set.

set -e

API_URL="${API_SERVICE_URL:-http://localhost:8000}"

echo "Dashboard starting — API URL: $API_URL"

# Replace the placeholder in nginx.conf with the real API URL
sed -i "s|__API_SERVICE_URL__|${API_URL}|g" /etc/nginx/conf.d/default.conf

exec nginx -g "daemon off;"
