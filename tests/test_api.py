import json
import time
import pytest

from scope1090.db import init_db, get_conn, insert_metrics
import scope1090.api as api_module
from scope1090.api import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / 'test.db')
    init_db(db_path)
    monkeypatch.setattr(api_module, 'LIVE_DB', db_path)
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c, db_path


def test_metrics_missing_param_returns_400(client):
    c, _ = client
    resp = c.get('/api/metrics')
    assert resp.status_code == 400
    assert b'metric' in resp.data


def test_metrics_returns_data(client):
    c, db_path = client
    now = int(time.time())
    conn = get_conn(db_path)
    insert_metrics(conn, now - 100, {'aircraft': 42.0})
    conn.close()

    resp = c.get(f'/api/metrics?metric=aircraft&from={now - 200}&to={now}')
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body['metric'] == 'aircraft'
    assert body['resolution'] == 'raw'
    assert len(body['data']) == 1
    assert body['data'][0][1] == 42.0


def test_metrics_auto_resolution_1h_for_long_range(client):
    c, db_path = client
    conn = get_conn(db_path)
    insert_metrics(conn, 3600, {'aircraft': 5.0})
    conn.close()

    resp = c.get('/api/metrics?metric=aircraft&from=0&to=90000')
    body = json.loads(resp.data)
    assert body['resolution'] == '1h'


def test_metrics_explicit_resolution_1h(client):
    c, db_path = client
    conn = get_conn(db_path)
    insert_metrics(conn, 3600, {'aircraft': 5.0})
    insert_metrics(conn, 3660, {'aircraft': 15.0})
    conn.close()

    resp = c.get('/api/metrics?metric=aircraft&from=0&to=7200&resolution=1h')
    body = json.loads(resp.data)
    assert body['resolution'] == '1h'
    assert len(body['data']) == 1
    assert body['data'][0][1] == pytest.approx(10.0)


def test_metrics_names(client):
    c, db_path = client
    conn = get_conn(db_path)
    insert_metrics(conn, 1000, {'aircraft': 1.0, 'max_range': 200.0})
    conn.close()

    resp = c.get('/api/metrics/names')
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert 'aircraft' in body['names']
    assert 'max_range' in body['names']


def test_metrics_invalid_timestamp_returns_400(client):
    c, _ = client
    resp = c.get('/api/metrics?metric=aircraft&from=abc&to=xyz')
    assert resp.status_code == 400
    assert b'integers' in resp.data


def test_status(client):
    c, _ = client
    resp = c.get('/api/status')
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert 'uptime_sec' in body
    assert 'db_size_bytes' in body
    assert 'last_collected' in body
    assert isinstance(body['uptime_sec'], (int, float))
