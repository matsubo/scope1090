const BASE = '/api';

export async function fetchMetrics(metric, from, to, resolution = 'auto') {
    const params = new URLSearchParams({ metric, from, to, resolution });
    const res = await fetch(`${BASE}/metrics?${params}`);
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
}

export async function fetchMetricNames() {
    const res = await fetch(`${BASE}/metrics/names`);
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
}

export async function fetchStatus() {
    const res = await fetch(`${BASE}/status`);
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
}
