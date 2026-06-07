document.addEventListener('DOMContentLoaded', () => {
    // Tab Switching
    const navItems = document.querySelectorAll('nav li');
    const sections = document.querySelectorAll('.tab-content');
    const title = document.getElementById('tab-title');
    const subtitle = document.getElementById('tab-subtitle');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tab = item.getAttribute('data-tab');
            
            navItems.forEach(i => i.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));

            item.classList.add('active');
            document.getElementById(`${tab}-section`).classList.add('active');

            // Update Header
            title.innerText = item.innerText.split(' ').slice(1).join(' ');
            subtitle.innerText = getSubtitle(tab);

            if (tab === 'config') loadConfig();
            if (tab === 'users') loadUsers();
            if (tab === 'logs') loadLogs();
            if (tab === 'features') loadSystemConfig();
        });
    });

    // Initialize Health Charts
    const cpuChart = initGauge('cpuChart', '#0070f3');
    const memChart = initGauge('memChart', '#00f0ff');

    // Stats Loop
    setInterval(() => fetchHealth(cpuChart, memChart), 10000);

    // Initial Load
    fetchHealth(cpuChart, memChart);
    
    // Config Save
    document.getElementById('save-config')?.addEventListener('click', saveConfig);
    
    // Feature Save
    document.getElementById('save-features')?.addEventListener('click', saveSystemConfig);

    // Restart API
    document.getElementById('restart-api')?.addEventListener('click', async () => {
        if (confirm("Are you sure you want to restart the main ML API?")) {
            try {
                const res = await fetch('/api/system/restart', { method: 'POST' });
                const data = await res.json();
                alert(data.message);
            } catch (e) {
                alert("Failed to send restart command.");
            }
        }
    });
});

function getSubtitle(tab) {
    const subtitles = {
        'health': 'Real-time monitoring of OSTEO AI infrastructure',
        'users': 'Manage registered practitioners and patient profiles',
        'config': 'Modify system-wide environment variables',
        'features': 'Master switches to pause or resume user app modules',
        'logs': 'Review application and model performance logs'
    };
    return subtitles[tab] || '';
}

async function fetchHealth(cpuChart, memChart) {
    try {
        const res = await fetch('/api/system/health');
        const data = await res.json();

        updateGauge(cpuChart, data.cpu);
        updateGauge(memChart, data.memory);

        document.getElementById('cpu-val').innerText = `${data.cpu.toFixed(1)}%`;
        document.getElementById('mem-val').innerText = `${data.memory.toFixed(1)}%`;

        // Update Status Indicator
        const dot = document.querySelector('.status-dot');
        const text = document.querySelector('.status-text');
        if (data.status === 'online') {
            dot.className = 'status-dot online';
            text.innerText = 'API ONLINE';
        } else {
            dot.className = 'status-dot offline';
            text.innerText = 'API OFFLINE';
        }

        // Also fetch DB status
        fetchDbStatus();
    } catch (e) {
        console.error("Health check failed", e);
    }
}

async function fetchDbStatus() {
    try {
        const res = await fetch('/api/db/status');
        const data = await res.json();
        const dot = document.getElementById('db-status-dot');
        const text = document.getElementById('db-status-text');

        if (data.status === 'connected') {
            dot.className = 'status-dot online';
            text.innerText = `DB CONNECTED (${data.users} Users)`;
        } else {
            dot.className = 'status-dot offline';
            text.innerText = 'DB DISCONNECTED';
        }
    } catch (e) {
        console.error("DB status check failed", e);
    }
}

async function loadConfig() {
    const container = document.getElementById('config-editor');
    container.innerHTML = '<p>Loading configuration...</p>';
    
    try {
        const res = await fetch('/api/config');
        const config = await res.json();
        
        container.innerHTML = Object.entries(config).map(([key, val]) => `
            <div class="config-row">
                <label>${key}</label>
                <input type="text" value="${val}" data-key="${key}">
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p class="error">Failed to load config.</p>';
    }
}

async function saveConfig() {
    const inputs = document.querySelectorAll('#config-editor input');
    const newConfig = {};
    inputs.forEach(input => {
        newConfig[input.getAttribute('data-key')] = input.value;
    });

    try {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newConfig)
        });
        const result = await res.json();
        alert(result.message);
    } catch (e) {
        alert("Failed to save config");
    }
}

async function loadSystemConfig() {
    try {
        const res = await fetch('/api/system/config');
        const config = await res.json();
        
        document.getElementById('toggle-clinical').checked = config.clinical_analysis;
        document.getElementById('toggle-xray').checked = config.xray_analysis;
        document.getElementById('toggle-appts').checked = config.appointments;
    } catch (e) {
        console.error("Failed to load system config", e);
    }
}

async function saveSystemConfig() {
    const newConfig = {
        clinical_analysis: document.getElementById('toggle-clinical').checked,
        xray_analysis: document.getElementById('toggle-xray').checked,
        appointments: document.getElementById('toggle-appts').checked
    };

    try {
        const res = await fetch('/api/system/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newConfig)
        });
        const result = await res.json();
        alert(result.message);
    } catch (e) {
        alert("Failed to update system features");
    }
}

async function loadUsers() {
    const tbody = document.querySelector('#users-table tbody');
    tbody.innerHTML = '<tr><td colspan="5">Loading users...</td></tr>';

    try {
        const res = await fetch('/api/users');
        const users = await res.json();

        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td>${user.phone || 'N/A'}</td>
                <td>${new Date().toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-sm btn-outline">Edit</button>
                    <button class="btn btn-sm btn-warning">Delete</button>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" class="error">Failed to load users.</td></tr>';
    }
}

async function loadLogs() {
    const tbody = document.querySelector('#logs-table tbody');
    tbody.innerHTML = '<tr><td colspan="5">Loading logs...</td></tr>';

    try {
        const res = await fetch('/api/predictions/logs');
        const logs = await res.json();

        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>${log.username}</td>
                <td>${log.age}</td>
                <td>${log.risk_pct}%</td>
                <td><span class="status-text" style="color: ${log.prediction === 1 ? 'var(--warning)' : 'var(--status-online)'}">${log.prediction === 1 ? 'High Risk' : 'Low Risk'}</span></td>
                <td>${log.date || 'Today'}</td>
            </tr>
        `).join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" class="error">Failed to load logs.</td></tr>';
    }
}

// Chart Helpers
function initGauge(id, color) {
    const ctx = document.getElementById(id).getContext('2d');
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [0, 100],
                backgroundColor: [color, '#222'],
                borderWidth: 0,
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '80%',
            plugins: { legend: { display: false }, tooltip: { enabled: false } }
        }
    });
}

function updateGauge(chart, val) {
    chart.data.datasets[0].data = [val, 100 - val];
    chart.update();
}
