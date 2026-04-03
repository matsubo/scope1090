const METRIC_META = {
    aircraft:      { label: 'Aircraft Seen',       unit: '',      color: '#3b82f6' },
    messages_rate: { label: 'Messages / s',         unit: 'msg/s', color: '#10b981' },
    max_range:     { label: 'Max Range',            unit: 'km',    color: '#f59e0b' },
    signal_mean:   { label: 'Signal Mean',          unit: 'dBFS',  color: '#8b5cf6' },
    signal_peak:   { label: 'Signal Peak',          unit: 'dBFS',  color: '#ec4899' },
    tracks_total:  { label: 'Tracks with Position', unit: '',      color: '#06b6d4' },
    airspy_rssi:   { label: 'Airspy RSSI',          unit: 'dB',    color: '#84cc16' },
    airspy_snr:    { label: 'Airspy SNR',           unit: 'dB',    color: '#f97316' },
};

export function buildOption(metric, data) {
    const meta = METRIC_META[metric] || { label: metric, unit: '', color: '#71717a' };
    return {
        backgroundColor: 'transparent',
        title: {
            text: meta.label,
            left: 'center',
            top: 4,
            textStyle: { fontSize: 12, color: '#a1a1aa', fontWeight: 500 },
        },
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#18181b',
            borderColor: '#3f3f46',
            textStyle: { color: '#e4e4e7', fontSize: 11 },
            formatter(params) {
                const d = new Date(params[0].value[0]);
                const val = params[0].value[1];
                return `${d.toLocaleString()}<br/>${val != null ? val.toFixed(2) : '—'} ${meta.unit}`;
            },
        },
        grid: { top: 36, bottom: 52, left: 48, right: 12 },
        xAxis: {
            type: 'time',
            axisLine: { lineStyle: { color: '#3f3f46' } },
            axisLabel: { color: '#71717a', fontSize: 10 },
            splitLine: { lineStyle: { color: '#27272a' } },
        },
        yAxis: {
            type: 'value',
            scale: true,
            axisLine: { show: false },
            axisLabel: { color: '#71717a', fontSize: 10 },
            splitLine: { lineStyle: { color: '#27272a' } },
        },
        dataZoom: [
            { type: 'inside', xAxisIndex: 0 },
            {
                type: 'slider',
                xAxisIndex: 0,
                height: 18,
                bottom: 8,
                borderColor: '#3f3f46',
                fillerColor: 'rgba(59,130,246,0.15)',
                handleStyle: { color: '#3b82f6' },
                textStyle: { color: '#71717a', fontSize: 9 },
            },
        ],
        series: [{
            type: 'line',
            data: data.map(([ts, v]) => [ts * 1000, v]),
            showSymbol: false,
            lineStyle: { width: 1.5, color: meta.color },
            areaStyle: { color: meta.color, opacity: 0.08 },
            emphasis: { disabled: true },
        }],
    };
}
