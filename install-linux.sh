#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This installer supports Linux only." >&2
  exit 1
fi

for command_name in python3 codex systemctl; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Required command not found: $command_name" >&2
    exit 1
  fi
done

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_path="$(command -v python3)"
codex_path="$(command -v codex)"
systemd_user_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/codex-quota-anchor"

mkdir -p "$systemd_user_dir" "$state_dir"

escape_systemd_value() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/%/%%/g'
}

escaped_python="$(escape_systemd_value "$python_path")"
escaped_script="$(escape_systemd_value "$script_dir/anchor.py")"
escaped_codex="$(escape_systemd_value "$codex_path")"

cat >"$systemd_user_dir/codex-quota-anchor.service" <<EOF
[Unit]
Description=Anchor the Codex five-hour quota window

[Service]
Type=oneshot
Environment="CODEX_QUOTA_CODEX_PATH=$escaped_codex"
ExecStart="$escaped_python" "$escaped_script" run
TimeoutStartSec=5min
EOF

cat >"$systemd_user_dir/codex-quota-anchor.timer" <<'EOF'
[Unit]
Description=Check the Codex quota window every 10 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=10min
Persistent=true
AccuracySec=30s
Unit=codex-quota-anchor.service

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now codex-quota-anchor.timer

echo "Installed codex-quota-anchor.timer"
echo "Runtime data: $state_dir"
echo "Check status: systemctl --user status codex-quota-anchor.timer"
