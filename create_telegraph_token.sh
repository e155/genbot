#!/usr/bin/env bash
set -euo pipefail

env_file="${1:-.env}"

if [[ ! -f "$env_file" ]]; then
  echo "ERROR: .env not found at: $env_file" >&2
  exit 1
fi

get_env_value() {
  local key="$1"
  local line
  line="$(rg -n "^\s*${key}\s*=" "$env_file" | head -n 1 || true)"
  if [[ -n "$line" ]]; then
    printf '%s' "${line#*=}" | sed 's/^["'\'']//; s/["'\'']$//'
  fi
}

default_short_name="genbot"
default_author_name="Generator Bot"
default_author_url="$(get_env_value BOTURL)"

read -r -p "Short name [$default_short_name]: " short_name
short_name="${short_name:-$default_short_name}"

read -r -p "Author name [$default_author_name]: " author_name
author_name="${author_name:-$default_author_name}"

read -r -p "Author URL [$default_author_url]: " author_url
author_url="${author_url:-$default_author_url}"

response="$(
  curl -sS -X POST "https://api.telegra.ph/createAccount" \
    -d "short_name=${short_name}" \
    -d "author_name=${author_name}" \
    -d "author_url=${author_url}"
)"

token="$(
  python - <<'PY'
import json, sys
try:
    data = json.loads(sys.stdin.read())
except Exception as e:
    print(f"ERROR: invalid JSON response: {e}", file=sys.stderr)
    sys.exit(1)
if not data.get("ok"):
    print(f"ERROR: API error: {data}", file=sys.stderr)
    sys.exit(1)
token = data.get("result", {}).get("access_token")
if not token:
    print("ERROR: access_token missing in response", file=sys.stderr)
    sys.exit(1)
print(token)
PY
)"

python - <<'PY' "$env_file" "$token"
import sys
from pathlib import Path

env_path = Path(sys.argv[1])
token = sys.argv[2]
key = "TELEGRAPH_TOKEN"

lines = env_path.read_text(encoding="utf-8").splitlines()
pattern = f"{key}="
updated = False
for i, line in enumerate(lines):
    if line.lstrip().startswith(pattern):
        lines[i] = f"{key}={token}"
        updated = True
        break
if not updated:
    lines.append(f"{key}={token}")

env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

echo "TELEGRAPH_TOKEN saved to $env_file"
