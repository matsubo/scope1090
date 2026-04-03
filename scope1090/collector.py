#!/usr/bin/env python3
import json
import os
import signal
import sys
import time
import urllib.request

from scope1090.db import get_conn, init_db, insert_metrics, run_maintenance

LIVE_DB = os.environ.get('SCOPE1090_DB', '/run/scope1090/live.db')
STATS_URL = os.environ.get('READSB_STATS_URL', 'file:///run/readsb/stats.json')
COLLECT_INTERVAL = 60


def fetch_stats(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())


def parse_metrics(stats):
    """Extract ADS-B metrics from readsb stats dict. Returns {name: float}."""
    result = {}
    last = stats.get('last1min', {})
    local = last.get('local', {})
    total = stats.get('total', {})
    airspy = stats.get('airspy', {})

    # Aircraft count is at root level in readsb stats
    if 'aircraft_with_pos' in stats:
        result['aircraft'] = float(stats['aircraft_with_pos'])

    # accepted is a list [adsb_count, mode_s_count, ...]
    if 'accepted' in local:
        accepted = local['accepted']
        total_accepted = sum(accepted) if isinstance(accepted, list) else accepted
        result['messages_rate'] = float(total_accepted) / 60.0

    # max_distance is in meters (no _m suffix in readsb JSON)
    if 'max_distance' in last:
        result['max_range'] = float(last['max_distance']) / 1000.0

    if 'signal' in local:
        result['signal_mean'] = float(local['signal'])
    if 'peak_signal' in local:
        result['signal_peak'] = float(local['peak_signal'])

    # tracks is a nested dict: {'all': N, 'single_message': M}
    if 'tracks' in total and isinstance(total['tracks'], dict):
        result['tracks_total'] = float(total['tracks'].get('all', 0))

    if 'rssi' in airspy:
        result['airspy_rssi'] = float(airspy['rssi'])
    if 'snr' in airspy:
        result['airspy_snr'] = float(airspy['snr'])

    return result


def main():
    db_dir = os.path.dirname(LIVE_DB)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    init_db(LIVE_DB)
    conn = get_conn(LIVE_DB)

    def _shutdown(signum, frame):
        conn.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    last_maintenance = 0

    while True:
        now = int(time.time())

        try:
            stats = fetch_stats(STATS_URL)
            metrics = parse_metrics(stats)
            if metrics:
                insert_metrics(conn, now, metrics)
        except Exception as e:
            print(f'[collector] {e}', file=sys.stderr)

        if now - last_maintenance > 86400:
            try:
                run_maintenance(LIVE_DB)
            except Exception as e:
                print(f'[collector] maintenance error: {e}', file=sys.stderr)
            last_maintenance = now

        elapsed = int(time.time()) - now
        time.sleep(max(0, COLLECT_INTERVAL - elapsed))


if __name__ == '__main__':
    main()
