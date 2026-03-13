#!/usr/bin/env bash
# deploy.sh — Build and deploy k4forge.org to a DigitalOcean Droplet
#
# Prerequisites:
#   - SSH access to droplet (ssh root@k4forge.org or similar)
#   - Caddy installed on droplet
#   - Node.js installed locally
#
# Usage:
#   cd web/
#   bash deploy/deploy.sh [user@host]

set -euo pipefail

REMOTE=${1:-root@k4forge.org}
REMOTE_DIR=/var/www/k4forge

echo "=== Building static site ==="
npm run build

echo "=== Uploading to ${REMOTE}:${REMOTE_DIR} ==="
ssh "${REMOTE}" "mkdir -p ${REMOTE_DIR}"
rsync -avz --delete out/ "${REMOTE}:${REMOTE_DIR}/"

echo "=== Uploading Caddyfile ==="
scp deploy/Caddyfile "${REMOTE}:/etc/caddy/Caddyfile"

echo "=== Reloading Caddy ==="
ssh "${REMOTE}" "systemctl reload caddy"

echo "=== Done. Site live at https://k4forge.org ==="
