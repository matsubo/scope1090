#!/usr/bin/env python3
import json
import math
import os
import signal
import sys
import time
import urllib.request

from scope1090.db import get_conn, init_db, insert_metrics, run_maintenance

LIVE_DB = os.environ.get('SCOPE1090_DB', '/run/scope1090/live.db')
STATS_URL = os.environ.get('READSB_STATS_URL', 'file:///run/readsb/stats.json')
AIRCRAFT_URL = os.environ.get('READSB_AIRCRAFT_URL', 'file:///run/readsb/aircraft.json')
RECEIVER_URL = os.environ.get('READSB_RECEIVER_URL', 'file:///run/readsb/receiver.json')
COLLECT_INTERVAL = 60


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())


def _percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    idx = (len(sorted_vals) - 1) * p
    lo, hi = int(idx), min(int(idx) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (idx - lo)


def _great_circle_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    d = math.radians
    dlat = d(lat2 - lat1)
    dlon = d(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(d(lat1)) * math.cos(d(lat2)) * math.sin(dlon / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def _cpu_temp():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            return float(f.read().strip()) / 1000.0
    except OSError:
        return None


def _mem_used_pct():
    try:
        data = {}
        with open('/proc/meminfo') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    data[parts[0].rstrip(':')] = int(parts[1])
        total = data.get('MemTotal', 0)
        if total == 0:
            return None
        free = data.get('MemFree', 0)
        buffers = data.get('Buffers', 0)
        cached = data.get('Cached', 0) + data.get('SReclaimable', 0) - data.get('Shmem', 0)
        used = total - free - buffers - cached
        return round(100.0 * used / total, 1)
    except OSError:
        return None


def parse_metrics(stats, aircraft_data=None, receiver=None):
    """Extract ADS-B and system metrics. Returns {name: float}."""
    result = {}
    last = stats.get('last1min', {})
    local = last.get('local', {})
    total = stats.get('total', {})
    airspy = stats.get('airspy', {})

    # Aircraft counts (root level in readsb stats)
    with_pos = stats.get('aircraft_with_pos', 0)
    without_pos = stats.get('aircraft_without_pos', 0)
    if 'aircraft_with_pos' in stats:
        result['aircraft'] = float(with_pos)
        result['aircraft_total'] = float(with_pos + without_pos)

    # Message rate (accepted is a list per DF type)
    if 'accepted' in local:
        accepted = local['accepted']
        total_accepted = sum(accepted) if isinstance(accepted, list) else float(accepted)
        result['messages_rate'] = total_accepted / 60.0

    # Positions per minute
    if 'position_count_total' in last:
        result['positions_rate'] = float(last['position_count_total'])

    # Max range from stats (meters → km)
    if 'max_distance' in last:
        result['max_range'] = float(last['max_distance']) / 1000.0

    # Signal levels
    if 'signal' in local:
        result['signal_mean'] = float(local['signal'])
    if 'peak_signal' in local:
        result['signal_peak'] = float(local['peak_signal'])
    if 'noise' in local:
        result['noise'] = float(local['noise'])
    if 'strong_signals' in local:
        result['strong_signals'] = float(local['strong_signals'])

    # SDR gain and estimated PPM error
    if 'gain_db' in stats:
        result['gain_db'] = float(stats['gain_db'])
    if 'estimated_ppm' in stats:
        result['estimated_ppm'] = float(stats['estimated_ppm'])

    # Tracks
    if 'tracks' in total and isinstance(total['tracks'], dict):
        result['tracks_total'] = float(total['tracks'].get('all', 0))

    # Airspy (optional, device-specific)
    if 'rssi' in airspy:
        result['airspy_rssi'] = float(airspy['rssi'])
    if 'snr' in airspy:
        result['airspy_snr'] = float(airspy['snr'])

    # Per-aircraft signal quartiles and range from aircraft.json
    if aircraft_data:
        rssi_vals = sorted(
            a['rssi'] for a in aircraft_data.get('aircraft', [])
            if 'rssi' in a and a.get('messages', 0) > 4 and a.get('seen', 999) < 30
            and a['rssi'] > -49.4
        )
        if rssi_vals:
            result['signal_q1']     = _percentile(rssi_vals, 0.25)
            result['signal_median'] = _percentile(rssi_vals, 0.50)
            result['signal_q3']     = _percentile(rssi_vals, 0.75)

        if receiver and 'lat' in receiver and 'lon' in receiver:
            rlat, rlon = receiver['lat'], receiver['lon']
            ranges = sorted(
                _great_circle_km(rlat, rlon, a['lat'], a['lon'])
                for a in aircraft_data.get('aircraft', [])
                if 'lat' in a and 'lon' in a and a.get('seen_pos', 999) < 60
            )
            if ranges:
                result['range_q1']     = _percentile(ranges, 0.25)
                result['range_median'] = _percentile(ranges, 0.50)
                result['range_q3']     = _percentile(ranges, 0.75)

    # System metrics
    temp = _cpu_temp()
    if temp is not None:
        result['cpu_temp'] = temp
    mem = _mem_used_pct()
    if mem is not None:
        result['mem_used_pct'] = mem

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
            stats = fetch_json(STATS_URL)
            aircraft_data, receiver = None, None
            try:
                aircraft_data = fetch_json(AIRCRAFT_URL)
                receiver = fetch_json(RECEIVER_URL)
            except Exception:
                pass
            metrics = parse_metrics(stats, aircraft_data, receiver)
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
