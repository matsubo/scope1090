const GREEN  = '#22c55e';
const BLUE   = '#3b82f6';
const CYAN   = '#06b6d4';
const PURPLE = '#8b5cf6';
const ORANGE = '#f97316';
const YELLOW = '#eab308';
const DGREEN = '#15803d';

function baseGrid() {
    return {
        backgroundColor: 'transparent',
        grid: { top: 36, bottom: 52, left: 56, right: 56 },
        xAxis: {
            type: 'time',
            axisLine: { lineStyle: { color: '#3f3f46' } },
            axisLabel: { color: '#71717a', fontSize: 10 },
            splitLine: { lineStyle: { color: '#27272a' } },
        },
        dataZoom: [
            { type: 'inside', xAxisIndex: 0 },
            {
                type: 'slider', xAxisIndex: 0,
                height: 18, bottom: 8,
                borderColor: '#3f3f46',
                fillerColor: 'rgba(59,130,246,0.15)',
                handleStyle: { color: '#3b82f6' },
                textStyle: { color: '#71717a', fontSize: 9 },
            },
        ],
    };
}

function titleOpt(text) {
    return { title: { text, left: 'center', top: 4, textStyle: { fontSize: 12, color: '#a1a1aa', fontWeight: 500 } } };
}

function yAxis(label, opts = {}) {
    return {
        type: 'value', scale: true,
        name: label, nameLocation: 'middle', nameGap: 40,
        nameTextStyle: { color: '#71717a', fontSize: 10 },
        axisLine: { show: false },
        axisLabel: { color: '#71717a', fontSize: 10 },
        splitLine: { lineStyle: { color: '#27272a' } },
        ...opts,
    };
}

function tooltipOpt(formatter) {
    return {
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#18181b',
            borderColor: '#3f3f46',
            textStyle: { color: '#e4e4e7', fontSize: 11 },
            formatter,
        },
    };
}

function line(name, data, color, opts = {}) {
    return {
        type: 'line', name, yAxisIndex: 0,
        data: data.map(([ts, v]) => [ts * 1000, v]),
        showSymbol: false,
        lineStyle: { width: 1.5, color },
        itemStyle: { color },
        emphasis: { disabled: true },
        ...opts,
    };
}

// Q1→Q3 green band using stacked areas
function bandSeries(q1, q3, name = '25th–75th pct') {
    const base   = q1.map(([ts, v]) => [ts * 1000, v]);
    const height = q1.map(([ts, v], i) => [ts * 1000, Math.max(0, (q3[i]?.[1] ?? v) - v)]);
    return [
        {
            type: 'line', name,
            data: base, stack: 'band',
            showSymbol: false,
            lineStyle: { width: 1, color: GREEN, opacity: 0.5 },
            itemStyle: { color: GREEN },
            areaStyle: { color: 'transparent' },
            emphasis: { disabled: true },
        },
        {
            type: 'line', name: '',
            data: height, stack: 'band',
            showSymbol: false,
            lineStyle: { width: 1, color: GREEN, opacity: 0.5 },
            itemStyle: { color: GREEN },
            areaStyle: { color: GREEN, opacity: 0.25 },
            emphasis: { disabled: true },
            tooltip: { show: false },
        },
    ];
}

function ts(v) { return new Date(v).toLocaleString(); }
function fmt(v, u) { return v != null ? `${v.toFixed(2)} ${u}` : '—'; }

// ── Chart builders ──────────────────────────────────────────────

export function buildMessagesOption(msgData, posData, strongData) {
    return {
        ...baseGrid(),
        ...titleOpt('Messages & Positions'),
        ...tooltipOpt(params => {
            const d = ts(params[0].value[0]);
            return params.map(p => `${p.marker}${p.seriesName}: ${fmt(p.value[1], '')}`).join('<br/>');
        }),
        grid: { top: 36, bottom: 52, left: 56, right: 56 },
        yAxis: [
            yAxis('msg/s'),
            yAxis('pos/min', { splitLine: { show: false } }),
        ],
        legend: { top: 4, right: 8, textStyle: { color: '#71717a', fontSize: 10 } },
        series: [
            line('Messages/s', msgData, BLUE),
            { ...line('Positions/min', posData, CYAN), yAxisIndex: 1 },
            {
                type: 'bar', name: 'Strong Signals',
                data: strongData.map(([ts, v]) => [ts * 1000, v]),
                itemStyle: { color: ORANGE, opacity: 0.6 },
                yAxisIndex: 0,
                barWidth: '60%',
            },
        ],
    };
}

export function buildAircraftOption(acData, totalData) {
    return {
        ...baseGrid(),
        ...titleOpt('Aircraft'),
        ...tooltipOpt(params => {
            return `${ts(params[0].value[0])}<br/>` +
                params.map(p => `${p.marker}${p.seriesName}: ${p.value[1] != null ? p.value[1].toFixed(0) : '—'}`).join('<br/>');
        }),
        yAxis: [yAxis('')],
        legend: { top: 4, right: 8, textStyle: { color: '#71717a', fontSize: 10 } },
        series: [
            line('With Position', acData, BLUE),
            line('Total', totalData, CYAN, { lineStyle: { width: 1.5, color: CYAN, type: 'dashed' } }),
        ],
    };
}

export function buildRangeOption(q1Data, q3Data, maxData, medianData) {
    return {
        ...baseGrid(),
        ...titleOpt('Range'),
        ...tooltipOpt(params => {
            const d = ts(params[0].value[0]);
            const filtered = params.filter(p => p.seriesName);
            return `${d}<br/>` + filtered.map(p => `${p.marker}${p.seriesName}: ${fmt(p.value[1], 'km')}`).join('<br/>');
        }),
        yAxis: [yAxis('km', { min: 0 })],
        legend: { top: 4, right: 8, textStyle: { color: '#71717a', fontSize: 10 } },
        series: [
            ...bandSeries(q1Data, q3Data, '25th–75th pct'),
            line('Max Range', maxData, BLUE),
            line('Median', medianData, '#888888', { lineStyle: { width: 1, color: '#888888', type: 'dashed' } }),
        ],
    };
}

export function buildSignalOption(q1Data, q3Data, medianData, peakData, noiseData) {
    return {
        ...baseGrid(),
        ...titleOpt('Signal Level'),
        ...tooltipOpt(params => {
            const d = ts(params[0].value[0]);
            const filtered = params.filter(p => p.seriesName);
            return `${d}<br/>` + filtered.map(p => `${p.marker}${p.seriesName}: ${fmt(p.value[1], 'dBFS')}`).join('<br/>');
        }),
        yAxis: [yAxis('dBFS')],
        legend: { top: 4, right: 8, textStyle: { color: '#71717a', fontSize: 10 } },
        series: [
            ...bandSeries(q1Data, q3Data, '25th–75th pct'),
            line('Median', medianData, '#888888'),
            line('Peak', peakData, BLUE),
            ...(noiseData.length ? [line('Noise', noiseData, DGREEN)] : []),
        ],
    };
}

export function buildSimpleOption(title, yLabel, color, data) {
    return {
        ...baseGrid(),
        ...titleOpt(title),
        ...tooltipOpt(params => {
            const v = params[0].value[1];
            return `${ts(params[0].value[0])}<br/>${fmt(v, yLabel)}`;
        }),
        yAxis: [yAxis(yLabel)],
        series: [line(title, data, color)],
    };
}
