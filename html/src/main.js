import * as echarts from 'echarts';
import { fetchMetrics } from './api.js';
import {
    buildMessagesOption,
    buildAircraftOption,
    buildRangeOption,
    buildSignalOption,
    buildSimpleOption,
} from './charts.js';

// Each chart: which metrics to fetch and how to build the option
const CHARTS = [
    {
        id: 'messages',
        metrics: ['messages_rate', 'positions_rate', 'strong_signals'],
        build: ([msg, pos, strong]) => buildMessagesOption(msg, pos, strong),
    },
    {
        id: 'aircraft',
        metrics: ['aircraft', 'aircraft_total'],
        build: ([ac, total]) => buildAircraftOption(ac, total),
    },
    {
        id: 'range',
        metrics: ['range_q1', 'range_q3', 'max_range', 'range_median'],
        build: ([q1, q3, max, med]) => buildRangeOption(q1, q3, max, med),
    },
    {
        id: 'signal',
        metrics: ['signal_q1', 'signal_q3', 'signal_median', 'signal_peak', 'noise'],
        build: ([q1, q3, med, peak, noise]) => buildSignalOption(q1, q3, med, peak, noise),
    },
    {
        id: 'tracks',
        metrics: ['tracks_total'],
        build: ([d]) => buildSimpleOption('Tracks', '', '#06b6d4', d),
    },
    {
        id: 'gain',
        metrics: ['gain_db'],
        build: ([d]) => buildSimpleOption('SDR Gain', 'dB', '#84cc16', d),
    },
    {
        id: 'ppm',
        metrics: ['estimated_ppm'],
        build: ([d]) => buildSimpleOption('Frequency Error', 'ppm', '#eab308', d),
    },
];

const POLL_MS = 60_000;
const instances = {};   // id → echarts instance
let currentRange = { from: 0, to: 0 };
let pollTimer = null;
let syncingZoom = false;

async function loadChart(chart, range) {
    const el = document.getElementById(`chart-${chart.id}`);
    if (!el) return;

    // Fetch all metrics for this chart in parallel; missing metrics return []
    const datasets = await Promise.all(
        chart.metrics.map(m =>
            fetchMetrics(m, range.from, range.to)
                .then(r => r.data)
                .catch(() => [])
        )
    );

    let inst = instances[chart.id];
    if (!inst) {
        inst = echarts.init(el, 'dark');
        instances[chart.id] = inst;

        inst.on('dataZoom', async () => {
            if (syncingZoom) return;
            const opt = inst.getOption();
            const dz = opt.dataZoom[0];
            if (dz.startValue == null) return;
            const from = Math.floor(dz.startValue / 1000);
            const to   = Math.floor(dz.endValue   / 1000);
            // Sync zoom on all other charts and re-fetch their data
            syncingZoom = true;
            await Promise.all(
                CHARTS.filter(c => c.id !== chart.id).map(async c => {
                    const inst2 = instances[c.id];
                    if (!inst2) return;
                    inst2.setOption({ dataZoom: [{ startValue: from * 1000, endValue: to * 1000 }] });
                    const ds = await Promise.all(
                        c.metrics.map(m => fetchMetrics(m, from, to).then(r => r.data).catch(() => []))
                    );
                    inst2.setOption(c.build(ds), { notMerge: true });
                    inst2.setOption({ dataZoom: [{ startValue: from * 1000, endValue: to * 1000 }] });
                })
            );
            syncingZoom = false;
            // Re-fetch own data too
            const ds = await Promise.all(
                chart.metrics.map(m => fetchMetrics(m, from, to).then(r => r.data).catch(() => []))
            );
            inst.setOption(chart.build(ds), { notMerge: true });
            inst.setOption({ dataZoom: [{ startValue: from * 1000, endValue: to * 1000 }] });
        });

        window.addEventListener('resize', () => inst.resize());
    }

    inst.setOption(chart.build(datasets), { notMerge: true });
}

async function refreshAll(range) {
    clearInterval(pollTimer);
    await Promise.all(CHARTS.map(c => loadChart(c, range)));
    pollTimer = setInterval(() => {
        const now = Math.floor(Date.now() / 1000);
        const span = currentRange.to - currentRange.from;
        currentRange = { from: now - span, to: now };
        CHARTS.forEach(c => loadChart(c, currentRange));
    }, POLL_MS);
}

// Lazy import controls
import('./controls.js').then(({ initControls }) => {
    initControls(range => {
        currentRange = range;
        refreshAll(range);
    });
});
