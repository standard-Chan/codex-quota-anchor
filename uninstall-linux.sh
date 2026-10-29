#!/usr/bin/env bash
set -euo pipefail

systemd_user_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

systemctl --user disable --now codex-quota-anchor.timer 2>/dev/null || true
rm -f \
  "$systemd_user_dir/codex-quota-anchor.timer" \
  "$systemd_user_dir/codex-quota-anchor.service"
systemctl --user daemon-reload
systemctl --user reset-failed codex-quota-anchor.service 2>/dev/null || true

echo "Removed codex-quota-anchor user timer and service"
