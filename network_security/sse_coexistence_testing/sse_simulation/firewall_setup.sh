#!/bin/bash
# Idempotent EC2 bootstrap: install Apache, configure UFW to allow only
# SSH + HTTP, enable the firewall. Safe to re-run.

set -euo pipefail

log()  { echo "[firewall_setup] $*" >&2; }

export DEBIAN_FRONTEND=noninteractive

log "updating apt"
apt-get update -y

log "installing apache2 and ufw"
apt-get install -y --no-install-recommends apache2 ufw

log "ensuring apache2 is enabled and running"
systemctl enable apache2
systemctl start  apache2

log "configuring ufw default-deny incoming"
ufw default deny incoming
ufw default allow outgoing

log "allowing ssh + http"
ufw allow 22/tcp
ufw allow 80/tcp

log "enabling ufw (non-interactive)"
ufw --force enable

log "current ufw status:"
ufw status verbose
