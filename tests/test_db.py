import pytest
import time
from scope1090.db import init_db, get_conn, insert_metrics, query_metrics, get_metric_names, run_maintenance


@pytest.fixture
def tmp_db(tmp_path):
    path = str(tmp_path / 'test.db')
    init_db(path)
    return path


def test_init_db_creates_table(tmp_db):
    conn = get_conn(tmp_db)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    conn.close()
    assert ('metrics',) in tables


def test_insert_and_query_raw(tmp_db):
    conn = get_conn(tmp_db)
    insert_metrics(conn, 1000, {'aircraft': 42.0, 'messages_rate': 1.5})
    conn.close()
    rows, res = query_metrics(tmp_db, 'aircraft', 900, 1100, 'raw')
    assert res == 'raw'
    assert len(rows) == 1
    assert rows[0][0] == 1000
    assert rows[0][1] == 42.0


def test_resolution_auto_raw_for_le_24h(tmp_db):
    conn = get_conn(tmp_db)
    insert_metrics(conn, 1000, {'aircraft': 10.0})
    conn.close()
    _, res = query_metrics(tmp_db, 'aircraft', 0, 86400, 'auto')
    assert res == 'raw'


def test_resolution_auto_1h_for_gt_24h(tmp_db):
    conn = get_conn(tmp_db)
    insert_metrics(conn, 1000, {'aircraft': 10.0})
    conn.close()
    _, res = query_metrics(tmp_db, 'aircraft', 0, 86401, 'auto')
    assert res == '1h'


def test_resolution_1h_groups_by_hour(tmp_db):
    conn = get_conn(tmp_db)
    insert_metrics(conn, 3600, {'aircraft': 10.0})
    insert_metrics(conn, 3660, {'aircraft': 20.0})
    conn.close()
    rows, res = query_metrics(tmp_db, 'aircraft', 0, 7200, '1h')
    assert res == '1h'
    assert len(rows) == 1
    assert rows[0][1] == pytest.approx(15.0)


def test_get_metric_names(tmp_db):
    conn = get_conn(tmp_db)
    insert_metrics(conn, 1000, {'aircraft': 1.0, 'messages_rate': 2.0})
    conn.close()
    names = get_metric_names(tmp_db)
    assert 'aircraft' in names
    assert 'messages_rate' in names


def test_run_maintenance_aggregates_old_data(tmp_db):
    conn = get_conn(tmp_db)
    old_ts = int(time.time()) - 31 * 86400
    hour_ts = (old_ts // 3600) * 3600
    insert_metrics(conn, hour_ts + 60,  {'aircraft': 10.0})
    insert_metrics(conn, hour_ts + 120, {'aircraft': 20.0})
    conn.close()

    run_maintenance(tmp_db)

    rows, _ = query_metrics(tmp_db, 'aircraft', hour_ts - 1, hour_ts + 3601, 'raw')
    assert len(rows) == 1
    assert rows[0][0] == hour_ts
    assert rows[0][1] == pytest.approx(15.0)
