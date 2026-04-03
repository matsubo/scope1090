#!/bin/bash
set -euo pipefail

INSTALL_DIR=/usr/share/scope1090
DATA_DIR=/var/lib/scope1090
SYSTEMD_DIR=/etc/systemd/system

echo "==> Installing scope1090"

# Build frontend if not already built
if [ ! -d scope1090/html/dist ]; then
    echo "==> Building frontend..."
    cd scope1090/html && npm install && npm run build && cd ../..
fi

# Install Python package
echo "==> Installing Python files..."
mkdir -p /usr/share
cp -r scope1090 /usr/share/
cp -r scope1090/html/dist "$INSTALL_DIR/html"
pip3 install --quiet flask

# Create data directory
mkdir -p "$DATA_DIR"

# Install systemd units
echo "==> Installing systemd units..."
cp scope1090/systemd/*.service scope1090/systemd/*.timer "$SYSTEMD_DIR/"
systemctl daemon-reload

# Install web server config (nginx preferred, lighttpd fallback)
if command -v nginx >/dev/null 2>&1; then
    echo "==> Configuring nginx..."
    cp scope1090/nginx/scope1090.conf /etc/nginx/sites-available/scope1090
    ln -sf /etc/nginx/sites-available/scope1090 /etc/nginx/sites-enabled/scope1090
    nginx -t && systemctl reload nginx
elif command -v lighttpd >/dev/null 2>&1; then
    echo "==> Configuring lighttpd..."
    cp scope1090/lighttpd/scope1090.conf /etc/lighttpd/conf-available/99-scope1090.conf
    lighty-enable-mod scope1090 || true
    service lighttpd reload
fi

# Enable and start services
echo "==> Enabling services..."
systemctl enable scope1090-restore.service \
                 scope1090-collector.service \
                 scope1090-api.service \
                 scope1090-persist.timer
systemctl start  scope1090-collector.service \
                 scope1090-api.service \
                 scope1090-persist.timer

echo ""
echo "scope1090 installed. Visit http://$(hostname -I | awk '{print $1}')/"
