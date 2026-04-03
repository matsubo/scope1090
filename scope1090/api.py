import os
import time

from flask import Flask, jsonify, request

from scope1090.db import query_metrics, get_metric_names

LIVE_DB = os.environ.get('SCOPE1090_DB', '/run/scope1090/live.db')

app = Flask(__name__)
_start_time = time.time()


@app.route('/api/metrics')
def metrics():
    metric = request.args.get('metric')
    if not metric:
        return jsonify({'error': 'metric parameter required'}), 400

    now = int(time.time())
    from_ts = int(request.args.get('from', now - 86400))
    to_ts = int(request.args.get('to', now))
    resolution = request.args.get('resolution', 'auto')

    rows, res = query_metrics(LIVE_DB, metric, from_ts, to_ts, resolution)

    return jsonify({
        'metric': metric,
        'from': from_ts,
        'to': to_ts,
        'resolution': res,
        'data': [[r[0], r[1]] for r in rows],
    })


@app.route('/api/metrics/names')
def metric_names():
    return jsonify({'names': get_metric_names(LIVE_DB)})


@app.route('/api/status')
def status():
    db_size = os.path.getsize(LIVE_DB) if os.path.exists(LIVE_DB) else 0
    return jsonify({
        'uptime_sec': int(time.time() - _start_time),
        'db_size_bytes': db_size,
        'db_path': LIVE_DB,
    })


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
