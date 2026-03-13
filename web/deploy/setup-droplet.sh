#!/usr/bin/env bash
# setup-droplet.sh — One-time setup for a fresh DigitalOcean Ubuntu droplet
#
# Run on the droplet:
#   curl -fsSL https://raw.githubusercontent.com/wardc/k4-engine/main/web/deploy/setup-droplet.sh | bash
#
# This installs Caddy, creates the web root, and enables the service.

set -euo pipefail

echo "=== Installing Caddy ==="
apt-get update
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update
apt-get install -y caddy

echo "=== Creating web root ==="
mkdir -p /var/www/k4forge
mkdir -p /var/log/caddy

echo "=== Enabling Caddy ==="
systemctl enable caddy
systemctl start caddy

echo "=== Done. Upload Caddyfile and site with deploy.sh ==="
