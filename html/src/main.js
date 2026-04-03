import * as echarts from 'echarts';
import { fetchMetrics } from './api.js';
import { buildOption } from './charts.js';
import { initControls } from './controls.js';

const METRICS = [
    'aircraft', 'aircraft_total',
    'messages_rate', 'positions_rate',
    'max_range', 'range_median', 'range_q1', 'range_q3',
    'signal_mean', 'signal_peak', 'noise',
    'signal_median', 'signal_q1', 'signal_q3',
    'strong_signals', 'tracks_total',
    'gain_db', 'estimated_ppm',
    'cpu_temp', 'mem_used_pct',
];
const POLL_MS = 60_000;

const charts = {};
let currentRange = { from: 0, to: 0 };
let pollTimer = null;
let syncingZoom = false;

function syncZoomToAll(from, to, sourceMetric) {
    if (syncingZoom) return;
    syncingZoom = true;
    for (const [metric, chart] of Object.entries(charts)) {
        if (metric === sourceMetric) continue;
        chart.setOption({ dataZoom: [{ startValue: from * 1000, endValue: to * 1000 }] });
    }
    syncingZoom = false;
}

async function loadChart(metric, range) {
    const el = document.getElementById(`chart-${metric}`);
    if (!el) return;

    let chart = charts[metric];
    if (!chart) {
        chart = echarts.init(el, 'dark');
        charts[metric] = chart;

        chart.on('dataZoom', async () => {
            if (syncingZoom) return;
            const opt = chart.getOption();
            const dz = opt.dataZoom[0];
            if (dz.startValue == null) return;
            const from = Math.floor(dz.startValue / 1000);
            const to   = Math.floor(dz.endValue   / 1000);
            syncZoomToAll(from, to, metric);
            try {
                const { data } = await fetchMetrics(metric, from, to);
                chart.setOption({ series: [{ data: data.map(([ts, v]) => [ts * 1000, v]) }] });
            } catch (e) {
                console.error(`[scope1090] dataZoom ${metric}: ${e.message}`);
            }
        });

        window.addEventListener('resize', () => chart.resize());
    }

    try {
        const { data } = await fetchMetrics(metric, range.from, range.to);
        chart.setOption(buildOption(metric, data), { notMerge: true });
    } catch (e) {
        console.error(`[scope1090] ${metric}: ${e.message}`);
    }
}

async function refreshAll(range) {
    clearInterval(pollTimer);
    await Promise.all(METRICS.map(m => loadChart(m, range)));
    pollTimer = setInterval(() => {
        const now = Math.floor(Date.now() / 1000);
        const span = currentRange.to - currentRange.from;
        currentRange = { from: now - span, to: now };
        Promise.all(METRICS.map(m => loadChart(m, currentRange)));
    }, POLL_MS);
}

initControls(range => {
    currentRange = range;
    refreshAll(range);
});
