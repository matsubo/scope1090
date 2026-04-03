# scope1090

ADS-B receiver performance monitoring dashboard — interactive charts, full-resolution history, minimal SD card writes.

Replaces the RRD/PNG pipeline of graphs1090 with a SQLite time-series store and [ECharts](https://echarts.apache.org/) interactive visualizations, designed to run on Raspberry Pi.

## Features

- **Full-resolution data** — every minute, no thinning for recent data
- **Interactive zoom/pan** — drag, scroll wheel, or preset buttons (2h / 24h / 7d / 30d)
- **RAM-first storage** — live database lives on tmpfs; SD card written only once per hour
- **ADS-B only** — aircraft count, message rate, max range, signal levels, tracks, Airspy RSSI/SNR
- **Lightweight** — Python 3 + stdlib + Flask, no collectd, no RRD

## Requirements

- Raspberry Pi running Raspberry Pi OS (or any Linux with systemd)
- [readsb](https://github.com/wiedehopf/readsb) or dump1090 producing `stats.json`
- Python 3.9+
- Node.js 18+ (needed to build the frontend during install)
- nginx or lighttpd

## Quick Install

```bash
git clone https://github.com/matsubo/scope1090
sudo bash scope1090/install.sh
```

The install script:
1. Builds the frontend (`npm install && npm run build` inside `html/`)
2. Installs Python package to `/usr/share/scope1090/`
3. Installs Flask via `pip3`
4. Installs systemd units and configures nginx or lighttpd

Then open `http://<raspberry-pi-ip>/` in your browser.

## Architecture

```
readsb/dump1090 (stats.json)
        ↓ every 60s
  collector.py
        ↓ INSERT
  /run/scope1090/live.db  (tmpfs = RAM)
        ↓ hourly cp (systemd timer)
  /var/lib/scope1090/archive.db  (SD card)

  api.py (Flask :5000)
        ← SELECT from live.db
        → /api/metrics
        → /api/metrics/names
        → /api/status

  nginx / lighttpd
        ← /usr/share/scope1090/html/  (Vite build)
        ← proxy /api/* → Flask
```

## Metrics Collected

| Metric | Description | Unit |
|--------|-------------|------|
| `aircraft` | Aircraft seen in last minute | count |
| `messages_rate` | Messages per second | msg/s |
| `max_range` | Maximum reception range | km |
| `signal_mean` | Mean signal level | dBFS |
| `signal_peak` | Peak signal level | dBFS |
| `tracks_total` | Total tracks with position | count |
| `airspy_rssi` | Airspy RSSI (if present) | dB |
| `airspy_snr` | Airspy SNR (if present) | dB |

## Data Retention

| Age | Resolution |
|-----|-----------|
| 0 – 30 days | 1-minute (raw) |
| 30 days – 1 year | 1-hour average |
| > 1 year | deleted |

## Development

```bash
# Install Python deps
pip3 install flask pytest

# Run tests
pytest tests/ -v

# Seed a test database and start API
python3 -c "
from scope1090.db import init_db, get_conn, insert_metrics
import time, os
os.makedirs('/tmp/scope1090', exist_ok=True)
db='/tmp/scope1090/live.db'
init_db(db)
conn=get_conn(db)
now=int(time.time())
for i in range(1440):
    insert_metrics(conn, now - i*60, {'aircraft': 40+i%15, 'messages_rate': 2.0,
        'max_range': 200.0, 'signal_mean': -15.0, 'signal_peak': -10.0, 'tracks_total': 500.0})
conn.close()
"
SCOPE1090_DB=/tmp/scope1090/live.db python3 -m scope1090.api &

# Start Vite dev server (proxies /api to Flask)
cd html
npm install
npm run dev
# Open http://localhost:5173
```

## File Structure

```
scope1090/                # repo root
├── scope1090/            # Python package
│   ├── __init__.py
│   ├── collector.py      # polls readsb stats.json every 60s
│   ├── api.py            # Flask JSON API
│   └── db.py             # SQLite helpers
├── html/
│   ├── src/
│   │   ├── main.js       # entry point, polling loop, zoom handler
│   │   ├── charts.js     # ECharts option builders
│   │   ├── api.js        # fetch wrappers
│   │   └── controls.js   # time range buttons
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── systemd/              # service and timer units
├── nginx/                # nginx reverse proxy config
├── lighttpd/             # lighttpd reverse proxy config
├── tests/
│   ├── test_db.py
│   ├── test_collector.py
│   └── test_api.py
└── install.sh            # Raspberry Pi install script
```

## License

MIT
