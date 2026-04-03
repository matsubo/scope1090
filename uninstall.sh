#!/bin/bash
set -euo pipefail

INSTALL_DIR=/usr/share/scope1090
DATA_DIR=/var/lib/scope1090
SYSTEMD_DIR=/etc/systemd/system

echo "==> Stopping and disabling services..."
systemctl stop  scope1090-api.service \
                scope1090-collector.service \
                scope1090-persist.timer 2>/dev/null || true
systemctl disable scope1090-restore.service \
                  scope1090-collector.service \
                  scope1090-api.service \
                  scope1090-persist.timer 2>/dev/null || true

echo "==> Removing systemd units..."
rm -f "$SYSTEMD_DIR/scope1090-api.service" \
      "$SYSTEMD_DIR/scope1090-collector.service" \
      "$SYSTEMD_DIR/scope1090-restore.service" \
      "$SYSTEMD_DIR/scope1090-persist.service" \
      "$SYSTEMD_DIR/scope1090-persist.timer"
systemctl daemon-reload

echo "==> Removing web server config..."
if command -v nginx >/dev/null 2>&1; then
    rm -f /etc/nginx/sites-enabled/scope1090 \
          /etc/nginx/sites-available/scope1090
    nginx -t && systemctl reload nginx 2>/dev/null || true
elif command -v lighttpd >/dev/null 2>&1; then
    lighty-disable-mod scope1090 2>/dev/null || true
    rm -f /etc/lighttpd/conf-available/99-scope1090.conf
    service lighttpd reload 2>/dev/null || true
fi

echo "==> Removing installed files..."
rm -rf "$INSTALL_DIR"

echo ""
echo "scope1090 uninstalled."
echo "Collected data in $DATA_DIR has been kept."
echo "To also remove historical data: rm -rf $DATA_DIR"
