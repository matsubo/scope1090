from scope1090.collector import parse_metrics


def test_parse_full_stats():
    stats = {
        'last1min': {
            'aircraft': 42,
            'local': {
                'accepted': 120,
                'signal': -15.5,
                'peak_signal': -10.0,
            },
            'max_distance_m': 250000,
        },
        'total': {
            'tracks_with_position': 1500,
        },
    }
    m = parse_metrics(stats)
    assert m['aircraft'] == 42.0
    assert m['messages_rate'] == 2.0        # 120 / 60
    assert m['max_range'] == 250.0          # 250000 / 1000
    assert m['signal_mean'] == -15.5
    assert m['signal_peak'] == -10.0
    assert m['tracks_total'] == 1500.0


def test_parse_missing_fields_returns_empty():
    assert parse_metrics({}) == {}
    assert parse_metrics({'last1min': {}, 'total': {}}) == {}


def test_parse_airspy_metrics():
    stats = {
        'last1min': {},
        'total': {},
        'airspy': {
            'rssi': -25.0,
            'snr': 18.5,
        },
    }
    m = parse_metrics(stats)
    assert m['airspy_rssi'] == -25.0
    assert m['airspy_snr'] == 18.5


def test_parse_partial_local():
    stats = {
        'last1min': {
            'aircraft': 5,
            'local': {'accepted': 60},
            # no signal fields
        },
        'total': {},
    }
    m = parse_metrics(stats)
    assert m['aircraft'] == 5.0
    assert m['messages_rate'] == 1.0
    assert 'signal_mean' not in m
    assert 'signal_peak' not in m
