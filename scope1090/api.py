import os
import time

from flask import Flask, Blueprint, jsonify, request

from scope1090.db import query_metrics, get_metric_names, get_conn

LIVE_DB = os.environ.get('SCOPE1090_DB', '/run/scope1090/live.db')
URL_PREFIX = os.environ.get('SCOPE1090_URL_PREFIX', '')
PORT = int(os.environ.get('SCOPE1090_PORT', '5000'))

app = Flask(__name__)
_start_time = time.time()

bp = Blueprint('api', __name__)


@bp.route('/api/metrics')
def metrics():
    metric = request.args.get('metric')
    if not metric:
        return jsonify({'error': 'metric parameter required'}), 400

    now = int(time.time())
    try:
        from_ts = int(request.args.get('from', now - 86400))
        to_ts = int(request.args.get('to', now))
    except ValueError:
        return jsonify({'error': 'from and to must be integers'}), 400

    resolution = request.args.get('resolution', 'auto')
    if resolution not in ('auto', 'raw', '1h'):
        return jsonify({'error': 'resolution must be auto, raw, or 1h'}), 400

    rows, res = query_metrics(LIVE_DB, metric, from_ts, to_ts, resolution)

    return jsonify({
        'metric': metric,
        'from': from_ts,
        'to': to_ts,
        'resolution': res,
        'data': [[r[0], r[1]] for r in rows],
    })


@bp.route('/api/metrics/names')
def metric_names():
    return jsonify({'names': get_metric_names(LIVE_DB)})


@bp.route('/api/status')
def status():
    db_size = os.path.getsize(LIVE_DB) if os.path.exists(LIVE_DB) else 0
    last_collected = None
    if os.path.exists(LIVE_DB):
        conn = get_conn(LIVE_DB)
        try:
            row = conn.execute('SELECT MAX(ts) FROM metrics').fetchone()
            last_collected = row[0]
        finally:
            conn.close()
    return jsonify({
        'uptime_sec': int(time.time() - _start_time),
        'db_size_bytes': db_size,
        'last_collected': last_collected,
    })


app.register_blueprint(bp, url_prefix=URL_PREFIX)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=PORT)
