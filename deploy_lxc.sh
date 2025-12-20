#!/usr/bin/env bash
set -euo pipefail

APP="genbot"

RD="\033[01;31m"
GN="\033[1;92m"
YW="\033[1;93m"
BL="\033[1;36m"
CL="\033[m"

INFO="${BL}[INFO]${CL}"
OK="${GN}[OK]${CL}"
ERR="${RD}[ERROR]${CL}"

header_info() {
  clear || true
  echo -e "${BL}== ${APP} Proxmox LXC Deployment ==${CL}"
  echo ""
}

msg_info() {
  echo -e "${INFO} $*"
}

msg_ok() {
  echo -e "${OK} $*"
}

msg_error() {
  echo -e "${ERR} $*" >&2
}

check_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    msg_error "$1 not found. Run this on the Proxmox host."
    exit 1
  fi
}

check_cmd pct

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

select_storage() {
  local storages=()
  if command -v pvesm >/dev/null 2>&1; then
    while IFS= read -r line; do
      storages+=("$line")
    done < <(pvesm status -content rootdir 2>/dev/null | awk 'NR>1 {print $1}')
  fi

  if [ "${#storages[@]}" -gt 0 ]; then
    echo "Available storages:"
    local i=1
    for s in "${storages[@]}"; do
      echo "  [$i] $s"
      i=$((i + 1))
    done
    local choice
    while true; do
      if [ -r /dev/tty ]; then
        read -r -p "Select storage [1-${#storages[@]}]: " choice </dev/tty
      else
        read -r -p "Select storage [1-${#storages[@]}]: " choice
      fi
      if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#storages[@]}" ]; then
        STORAGE="${storages[$((choice - 1))]}"
        break
      fi
      echo "Invalid choice. Try again."
    done
  else
    prompt STORAGE "Storage name" "local-lvm"
    STORAGE="${STORAGE:-local-lvm}"
  fi
}

header_info

STORAGE=""

prompt CTID "Container ID"
prompt HOSTNAME "Hostname" "genbot"
prompt TEMPLATE "Ubuntu 24.04 template path (e.g. local:vztmpl/ubuntu-24.04-standard_24.04-1_amd64.tar.zst)"
select_storage
STORAGE="${STORAGE:-local-lvm}"
prompt BRIDGE "Network bridge" "vmbr0"
prompt NET_MODE "Network mode (dhcp/static)" "dhcp"
NET_MODE="${NET_MODE:-dhcp}"
prompt DISK "Disk size (e.g. 8G)" "8G"
prompt MEMORY "Memory MB" "1024"
prompt SWAP "Swap MB" "512"
prompt UNPRIV "Unprivileged (1/0)" "1"

echo ""
msg_info "Enter .env values"
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

echo ""
NET_MODE_LOWER="$(printf '%s' "$NET_MODE" | tr '[:upper:]' '[:lower:]')"
if [ "$NET_MODE_LOWER" = "static" ]; then
  prompt STATIC_IP "Static IP (e.g. 192.168.1.50/24)"
  prompt GATEWAY "Gateway (e.g. 192.168.1.1)"
  NET_CONF="name=eth0,bridge=${BRIDGE},ip=${STATIC_IP},gw=${GATEWAY}"
else
  NET_CONF="name=eth0,bridge=${BRIDGE},ip=dhcp"
fi

msg_info "Creating container..."
pct create "$CTID" "$TEMPLATE" \
  --hostname "$HOSTNAME" \
  --storage "$STORAGE" \
  --rootfs "${STORAGE}:${DISK}" \
  --memory "$MEMORY" \
  --swap "$SWAP" \
  --net0 "$NET_CONF" \
  --unprivileged "$UNPRIV"

msg_info "Starting container..."
pct start "$CTID"

msg_info "Uploading project..."
WORKDIR="$(pwd)"
TMP_TAR="$(mktemp -t genbot.XXXXXX.tar.gz)"
tar --exclude .git --exclude .venv --exclude __pycache__ --exclude generator.db -czf "$TMP_TAR" -C "$WORKDIR" .
pct push "$CTID" "$TMP_TAR" /root/genbot.tar.gz
rm -f "$TMP_TAR"

msg_info "Configuring container..."
pct exec "$CTID" -- bash -lc "apt-get update && apt-get install -y python3-venv python3-pip && mkdir -p /opt/genbot && tar -xzf /root/genbot.tar.gz -C /opt/genbot && rm -f /root/genbot.tar.gz"

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
pct exec "$CTID" -- bash -lc "cat > /etc/systemd/system/genbot.service <<'UNIT'\n[Unit]\nDescription=Genbot\nAfter=network-online.target\nWants=network-online.target\n\n[Service]\nType=simple\nWorkingDirectory=/opt/genbot\nExecStart=/opt/genbot/.venv/bin/python /opt/genbot/bot.py\nRestart=always\nRestartSec=5\nEnvironment=PYTHONUNBUFFERED=1\n\n[Install]\nWantedBy=multi-user.target\nUNIT\nsystemctl daemon-reload && systemctl enable --now genbot.service"

msg_ok "Done. Container $CTID is running genbot."
