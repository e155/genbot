#!/usr/bin/env bash
set -euo pipefail

APP="genbot"
var_cpu=1
var_ram=256
var_disk=4
var_os="ubuntu"
var_version="24.04"
var_unprivileged=1
var_net="dhcp"

if command -v curl >/dev/null 2>&1; then
  source <(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/misc/build.func)
elif command -v wget >/dev/null 2>&1; then
  source <(wget -qO- https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/misc/build.func)
else
  echo "curl or wget not found. Run this on the Proxmox host." >&2
  exit 1
fi

if ! command -v pct >/dev/null 2>&1; then
  msg_error "pct not found. Run this on the Proxmox host."
  exit 1
fi

prompt() {
  local var_name="$1"
  local prompt_text="$2"
  local default_value="${3:-}"
  local input

  if [ -n "$default_value" ]; then
    if [ -r /dev/tty ]; then
      read -r -p "$prompt_text [$default_value]: " input </dev/tty
    else
      read -r -p "$prompt_text [$default_value]: " input
    fi
    if [ -z "$input" ]; then
      input="$default_value"
    fi
  else
    if [ -r /dev/tty ]; then
      read -r -p "$prompt_text: " input </dev/tty
    else
      read -r -p "$prompt_text: " input
    fi
  fi

  printf -v "$var_name" '%s' "$input"
}

prompt_secret() {
  local var_name="$1"
  local prompt_text="$2"
  local input

  if [ -r /dev/tty ]; then
    read -r -s -p "$prompt_text: " input </dev/tty
  else
    read -r -s -p "$prompt_text: " input
  fi
  echo ""
  printf -v "$var_name" '%s' "$input"
}

env_quote() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

header_info "$APP"
variables
color
catch_errors
DIAGNOSTICS="no"
type maxkeys_check >/dev/null 2>&1 && maxkeys_check
type pve_check >/dev/null 2>&1 && pve_check
type arch_check >/dev/null 2>&1 && arch_check

start
build_container

if [ -z "${CTID:-}" ] && [ -n "${CT_ID:-}" ]; then
  CTID="$CT_ID"
fi
if [ -z "${CTID:-}" ]; then
  msg_error "CTID not set after build_container."
  exit 1
fi

echo ""
echo "== .env values =="
prompt LANGUAGE "LANGUAGE (en/ru)" "ru"
prompt_secret TOKEN "TOKEN"
prompt CHANNELID "CHANNELID"
prompt ADMIN_USER_ID "ADMIN_USER_ID"
prompt BOTURL "BOTURL"
prompt GENERATORNAME "GENERATORNAME"
prompt GENERATORADDR "GENERATORADDR"
prompt INTERVAL "INTERVAL (seconds)" "60"
prompt REPORTH "REPORTH (0-23)" "7"
prompt REPORTM "REPORTM (0-59)" "0"
prompt TANK_CAPACITY "TANK_CAPACITY" "240"
prompt FUEL_CONSUMPTION "FUEL_CONSUMPTION" "16"
prompt INITIAL_FUEL "INITIAL_FUEL" "190"
prompt LOW_FUEL_HOURS "LOW_FUEL_HOURS" "4"

msg_info "Fetching project..."
pct exec "$CTID" -- bash -lc "apt-get update && apt-get install -y python3-venv python3-pip curl tar && mkdir -p /opt/genbot && curl -fsSL -L https://github.com/e155/genbot/archive/refs/heads/master.tar.gz -o /tmp/genbot.tar.gz && tar -xzf /tmp/genbot.tar.gz -C /opt/genbot --strip-components=1 && rm -f /tmp/genbot.tar.gz"

ENV_TMP="$(mktemp -t genbot.env.XXXXXX)"
cat > "$ENV_TMP" <<EOF
LANGUAGE="$(env_quote "$LANGUAGE")"
TOKEN="$(env_quote "$TOKEN")"
CHANNELID="$(env_quote "$CHANNELID")"
ADMIN_USER_ID="$(env_quote "$ADMIN_USER_ID")"
BOTURL="$(env_quote "$BOTURL")"

GENERATORNAME="$(env_quote "$GENERATORNAME")"
GENERATORADDR="$(env_quote "$GENERATORADDR")"
INTERVAL=$INTERVAL
REPORTH=$REPORTH
REPORTM=$REPORTM

TANK_CAPACITY=$TANK_CAPACITY
FUEL_CONSUMPTION=$FUEL_CONSUMPTION
INITIAL_FUEL=$INITIAL_FUEL
LOW_FUEL_HOURS=$LOW_FUEL_HOURS
EOF

pct push "$CTID" "$ENV_TMP" /opt/genbot/.env
rm -f "$ENV_TMP"

pct exec "$CTID" -- bash -lc "cd /opt/genbot && python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt"

msg_info "Installing systemd service..."
SERVICE_TMP="$(mktemp -t genbot.service.XXXXXX)"
cat > "$SERVICE_TMP" <<'UNIT'
[Unit]
Description=Genbot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/genbot
ExecStart=/opt/genbot/.venv/bin/python /opt/genbot/bot.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
UNIT
pct push "$CTID" "$SERVICE_TMP" /etc/systemd/system/genbot.service
rm -f "$SERVICE_TMP"
pct exec "$CTID" -- bash -lc "systemctl daemon-reload && systemctl enable --now genbot.service"

msg_ok "Done. Container $CTID is running genbot."
