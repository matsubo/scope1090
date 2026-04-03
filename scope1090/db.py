import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS metrics (
    ts    INTEGER NOT NULL,
    name  TEXT    NOT NULL,
    value REAL    NOT NULL,
    PRIMARY KEY (ts, name)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_name_ts ON metrics (name, ts);
"""


def get_conn(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db(path):
    conn = get_conn(path)
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()


def insert_metrics(conn, ts, metrics):
    """Insert a dict of {name: value} at timestamp ts (Unix seconds)."""
    rows = [(ts, name, float(value)) for name, value in metrics.items()]
    conn.executemany(
        "INSERT OR REPLACE INTO metrics (ts, name, value) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()


def query_metrics(path, name, from_ts, to_ts, resolution='auto'):
    """Return (rows, resolution_used). rows = list of (ts, value)."""
    span = to_ts - from_ts
    if resolution == 'auto':
        resolution = 'raw' if span <= 86400 else '1h'

    conn = get_conn(path)
    if resolution == '1h':
        sql = """
            SELECT (ts / 3600) * 3600 AS bucket, AVG(value)
            FROM metrics
            WHERE name = ? AND ts >= ? AND ts <= ?
            GROUP BY bucket
            ORDER BY bucket
        """
    else:
        sql = """
            SELECT ts, value FROM metrics
            WHERE name = ? AND ts >= ? AND ts <= ?
            ORDER BY ts
        """
    rows = conn.execute(sql, (name, from_ts, to_ts)).fetchall()
    conn.close()
    return rows, resolution


def get_metric_names(path):
    """Return sorted list of distinct metric names."""
    conn = get_conn(path)
    rows = conn.execute(
        "SELECT DISTINCT name FROM metrics ORDER BY name"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def run_maintenance(path):
    """Aggregate data older than 30 days to hourly; delete data older than 1 year."""
    conn = get_conn(path)
    conn.executescript("""
        INSERT OR REPLACE INTO metrics (ts, name, value)
            SELECT (ts / 3600) * 3600, name, AVG(value)
            FROM metrics
            WHERE ts < strftime('%s', 'now', '-30 days')
            GROUP BY (ts / 3600), name;

        DELETE FROM metrics
            WHERE ts < strftime('%s', 'now', '-30 days')
              AND ts % 3600 != 0;

        DELETE FROM metrics
            WHERE ts < strftime('%s', 'now', '-1 year');
    """)
    conn.commit()
    conn.close()
