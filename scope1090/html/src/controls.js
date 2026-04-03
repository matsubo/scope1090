const PRESETS = [
    { label: '2h',  seconds: 7200 },
    { label: '24h', seconds: 86400 },
    { label: '7d',  seconds: 604800 },
    { label: '30d', seconds: 2592000 },
];

export function initControls(onRangeChange) {
    const bar = document.getElementById('controls');
    let active = null;

    PRESETS.forEach(({ label, seconds }) => {
        const btn = document.createElement('button');
        btn.textContent = label;
        btn.className = 'btn';
        btn.dataset.seconds = seconds;
        btn.onclick = () => {
            if (active) active.classList.remove('active');
            btn.classList.add('active');
            active = btn;
            const now = Math.floor(Date.now() / 1000);
            onRangeChange({ from: now - seconds, to: now });
        };
        bar.appendChild(btn);
    });

    // Activate '24h' by default
    bar.querySelector('[data-seconds="86400"]').click();
}
