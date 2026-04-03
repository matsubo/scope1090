import * as echarts from 'echarts';
import { fetchMetrics } from './api.js';
import { buildOption } from './charts.js';
import { initControls } from './controls.js';

const METRICS = [
    'aircraft', 'messages_rate', 'max_range',
    'signal_mean', 'signal_peak', 'tracks_total',
];
const POLL_MS = 60_000;

const charts = {};
let currentRange = { from: 0, to: 0 };
let pollTimer = null;

async function loadChart(metric, range) {
    const el = document.getElementById(`chart-${metric}`);
    if (!el) return;

    let chart = charts[metric];
    if (!chart) {
        chart = echarts.init(el, 'dark');
        charts[metric] = chart;

        // Re-query when user zooms/pans via dataZoom
        chart.on('dataZoom', async () => {
            const opt = chart.getOption();
            const dz = opt.dataZoom[0];
            if (dz.startValue == null) return;
            // startValue/endValue are in ms (ECharts time axis)
            const from = Math.floor(dz.startValue / 1000);
            const to   = Math.floor(dz.endValue   / 1000);
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
