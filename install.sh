#!/bin/bash
set -euo pipefail

# Resolve the directory containing this script (the scope1090 package dir)
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

INSTALL_DIR=/usr/share/scope1090
DATA_DIR=/var/lib/scope1090
SYSTEMD_DIR=/etc/systemd/system

echo "==> Installing scope1090"

# Always rebuild frontend (ensures base path and config changes are applied)
echo "==> Building frontend..."
rm -rf "$SCRIPT_DIR/html/dist"
cd "$SCRIPT_DIR/html" && npm install && npm run build

# Install Python package to /usr/share/scope1090/
echo "==> Installing Python files..."
rm -rf "$INSTALL_DIR"
cp -r "$SCRIPT_DIR/scope1090" /usr/share/

# Install built frontend (nginx/lighttpd root = $INSTALL_DIR/html)
mkdir -p "$INSTALL_DIR/html"
cp -r "$SCRIPT_DIR/html/dist/." "$INSTALL_DIR/html/"
# Install Python dependencies into an isolated virtualenv (PEP 668 / Bookworm compatible)
VENV="$INSTALL_DIR/venv"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"

# Create data directory
mkdir -p "$DATA_DIR"

# Install systemd units
echo "==> Installing systemd units..."
cp "$SCRIPT_DIR/systemd/"*.service "$SCRIPT_DIR/systemd/"*.timer "$SYSTEMD_DIR/"
systemctl daemon-reload

# Install web server config (nginx preferred, lighttpd fallback)
if command -v nginx >/dev/null 2>&1; then
    echo "==> Configuring nginx..."
    cp "$SCRIPT_DIR/nginx/scope1090.conf" /etc/nginx/sites-available/scope1090
    ln -sf /etc/nginx/sites-available/scope1090 /etc/nginx/sites-enabled/scope1090
    nginx -t && systemctl reload nginx
elif command -v lighttpd >/dev/null 2>&1; then
    echo "==> Configuring lighttpd..."
    cp "$SCRIPT_DIR/lighttpd/scope1090.conf" /etc/lighttpd/conf-available/99-scope1090.conf
    lighty-enable-mod scope1090 || true
    service lighttpd reload
fi

# Enable and start services
echo "==> Enabling services..."
systemctl enable scope1090-restore.service \
                 scope1090-collector.service \
                 scope1090-api.service \
                 scope1090-persist.timer
systemctl restart scope1090-collector.service \
                  scope1090-api.service
systemctl start   scope1090-persist.timer 2>/dev/null || true

echo ""
echo "scope1090 installed. Visit http://$(hostname -I | awk '{print $1}')/scope1090/"
