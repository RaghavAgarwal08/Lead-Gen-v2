// Override fetch to include authorization header and handle 401s globally
const originalFetch = window.fetch;
window.fetch = async function (url, options = {}) {
    options.headers = options.headers || {};
    
    // Read password from localStorage
    const savedPassword = localStorage.getItem('app_password');
    if (savedPassword) {
        options.headers['X-App-Password'] = savedPassword;
    }
    
    try {
        const response = await originalFetch(url, options);
        if (response.status === 401) {
            // Invalid credentials, prompt user
            showLoginModal();
        }
        return response;
    } catch (error) {
        throw error;
    }
};

function showLoginModal() {
    localStorage.removeItem('app_password');
    const modal = document.getElementById('login-modal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function hideLoginModal() {
    const modal = document.getElementById('login-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// State Manager
let state = {
    activeTab: 'dashboard',
    pipelineStatus: {
        is_running: false,
        current_step: 'Idle',
        progress: 0,
        error: null,
        logs: [],
        leads_count: 0
    },
    leads: [],
    historyLeads: [],
    selectedLead: null,
    pollingInterval: null
};

// DOM Elements
const menuButtons = document.querySelectorAll('.menu-item');
const tabPanels = document.querySelectorAll('.tab-panel');
const pageTitle = document.getElementById('page-title');
const pageDesc = document.getElementById('page-desc');
const systemStatusDot = document.getElementById('system-status-dot');
const systemStatusLabel = document.getElementById('system-status-label');

const limitInput = document.getElementById('limit-input');
const emailInput = document.getElementById('email-input');
const pipelineForm = document.getElementById('pipeline-form');
const startBtn = document.getElementById('start-btn');
const cancelBtn = document.getElementById('cancel-btn');
const resetBtn = document.getElementById('reset-btn');

const consolePulse = document.getElementById('console-pulse');
const progressFill = document.getElementById('progress-fill');
const progressVal = document.getElementById('progress-val');
const consoleLogs = document.getElementById('console-logs');

const searchInput = document.getElementById('search-input');
const leadsCountBadge = document.getElementById('leads-count-badge');
const leadsList = document.getElementById('leads-list');

const historySearchInput = document.getElementById('history-search-input');
const historyCountBadge = document.getElementById('history-count-badge');
const historyList = document.getElementById('history-list');
const clearHistoryBtn = document.getElementById('clear-history-btn');

const detailsBackBtn = document.getElementById('details-back-btn');
const detailsMenuBtn = document.getElementById('details-menu-btn');
const leadDetailContent = document.getElementById('lead-detail-content');

const sidebarExports = document.getElementById('sidebar-exports-container');

// Stats and Quota Elements
const runtimeVal = document.getElementById('runtime-val');
const genRateVal = document.getElementById('gen-rate-val');
const replyRateVal = document.getElementById('reply-rate-val');
const replyRateBar = document.getElementById('reply-rate-bar');


// Tab Configuration
const tabMeta = {
    dashboard: { title: 'Dashboard', desc: 'Run pipeline, monitor execution, and compile sales reports.' },
    directory: { title: 'Prospects Directory', desc: 'Explore qualified target companies and access detailed dossiers.' },
    history: { title: 'Lead History', desc: 'Browse the persistent all-time catalog of generated target leads.' },
    details: { title: 'Lead Dossier', desc: 'Deep dive into company intelligence, contact details, and outreach pitch angles.' },
    settings: { title: 'System Credentials', desc: 'Verify API keys and email delivery setups.' }
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    setupTabNavigation();
    setupFormControls();
    checkPipelineStatus();
    loadLeads();
    loadHistory();
    checkApiCredentials();
    
    // Periodically poll status if page was loaded during active run
    state.pollingInterval = setInterval(checkPipelineStatus, 2000);
    
    // Smooth 1-second timer for live runtime display
    setInterval(updateRuntimeCounter, 1000);
});


// Tab Navigation Logic
function setupTabNavigation() {
    menuButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            if (tabId) {
                switchTab(tabId);
            }
        });
    });

    detailsBackBtn.addEventListener('click', () => {
        if (state.lastDirectoryTab === 'history') {
            switchTab('history');
        } else {
            switchTab('directory');
        }
    });

    // Logout / Lock Dashboard Button
    const logoutBtn = document.getElementById('logout-menu-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to lock the dashboard?')) {
                showLoginModal();
                const passwordInput = document.getElementById('password-input');
                if (passwordInput) passwordInput.value = '';
            }
        });
    }
}

function switchTab(tabId) {
    state.activeTab = tabId;
    if (tabId === 'directory' || tabId === 'history') {
        state.lastDirectoryTab = tabId;
    }
    
    // Update menu button active states
    menuButtons.forEach(btn => {
        if (btn.getAttribute('data-tab') === tabId) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update panel active states
    tabPanels.forEach(panel => {
        if (panel.id === `${tabId}-panel`) {
            panel.classList.add('active');
        } else {
            panel.classList.remove('active');
        }
    });

    // Update Title & Desc
    if (tabMeta[tabId]) {
        pageTitle.textContent = tabMeta[tabId].title;
        pageDesc.textContent = tabMeta[tabId].desc;
    }

    // Tab Specific Loading Actions
    if (tabId === 'directory') {
        loadLeads();
    } else if (tabId === 'history') {
        loadHistory();
    } else if (tabId === 'settings') {
        checkApiCredentials();
    }
}

// Form Syncing & Controls
function setupFormControls() {
    limitInput.addEventListener('input', (e) => {
        let val = parseInt(e.target.value);
        if (isNaN(val)) return;
        if (val > 50) {
            alert("Sorry, the limit is 50.");
            e.target.value = 50;
        } else if (val < 1) {
            e.target.value = 1;
        }
    });

    pipelineForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (state.pipelineStatus.is_running) return;

        const limit = parseInt(limitInput.value);
        if (isNaN(limit) || limit < 1) {
            alert('Please enter a valid number of leads (at least 1).');
            return;
        }
        if (limit > 50) {
            alert('Sorry, the limit is 50.');
            return;
        }
        const email = emailInput.value.trim();

        const emailConfirmText = email ? `\nEmail Report Recipient: ${email}` : '\nEmail Report Recipient: (none - left blank)';
        const confirmed = confirm(`Are you sure you want to produce exactly ${limit} leads?${emailConfirmText}`);
        if (!confirmed) {
            return;
        }

        try {
            const res = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ limit, email })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Failed to start pipeline');
            }

            consoleLogs.innerHTML = `<div class="log-line text-muted">[SYSTEM] Requesting pipeline start...</div>`;
            state.pipelineStatus.is_running = true;
            updateUIStatus();
            
            // Switch menu views if needed
            switchTab('dashboard');
            
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    });

    cancelBtn.addEventListener('click', async () => {
        if (confirm('Are you sure you want to cancel the active lead generation run?')) {
            cancelBtn.disabled = true;
            cancelBtn.querySelector('span').textContent = 'Cancelling...';
            await fetch('/api/cancel', { method: 'POST' });
            checkPipelineStatus();
        }
    });

    resetBtn.addEventListener('click', async () => {
        if (confirm('Are you sure you want to reset the pipeline state? Current logs will be cleared.')) {
            await fetch('/api/reset', { method: 'POST' });
            checkPipelineStatus();
        }
    });

    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', async () => {
            if (confirm('Are you sure you want to permanently delete all lead history? This cannot be undone.')) {
                await fetch('/api/clear-history', { method: 'POST' });
                loadHistory();
            }
        });
    }

    // Setup Live search filter
    searchInput.addEventListener('input', () => {
        renderLeadsList();
    });
    if (historySearchInput) {
        historySearchInput.addEventListener('input', () => {
            renderHistoryList();
        });
    }
    // Setup Download Report listeners to prevent downloading JSON errors
    const dlDocxBtn = document.getElementById('dl-docx');
    const dlCsvBtn = document.getElementById('dl-csv');

    if (dlDocxBtn) {
        dlDocxBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                const res = await fetch('/api/download/docx');
                if (!res.ok) {
                    const errData = await res.json();
                    alert(errData.detail || 'DOCX report not found. Please run the pipeline first.');
                    return;
                }
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'Timidly_Prospects_Report.docx';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } catch (err) {
                alert('Failed to download report.');
            }
        });
    }

    if (dlCsvBtn) {
        dlCsvBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                const res = await fetch('/api/download/csv');
                if (!res.ok) {
                    const errData = await res.json();
                    alert(errData.detail || 'CSV report not found. Please run the pipeline first.');
                    return;
                }
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'Timidly_Prospects_Report.csv';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } catch (err) {
                alert('Failed to download CSV.');
            }
        });
    }

    // Setup Authentication Submit listeners
    const submitPassBtn = document.getElementById('submit-password-btn');
    const passwordInput = document.getElementById('password-input');
    const loginErrorHint = document.getElementById('login-error-hint');

    if (submitPassBtn && passwordInput) {
        submitPassBtn.addEventListener('click', handleAuthenticationSubmit);
        passwordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleAuthenticationSubmit();
            }
        });
    }

    async function handleAuthenticationSubmit() {
        const password = passwordInput.value.trim();
        if (!password) return;
        
        localStorage.setItem('app_password', password);
        
        try {
            if (loginErrorHint) loginErrorHint.style.display = 'none';
            const response = await originalFetch('/api/config', {
                headers: { 'X-App-Password': password }
            });
            if (response.ok) {
                hideLoginModal();
                checkPipelineStatus();
                loadLeads();
                loadHistory();
                checkApiCredentials();
            } else {
                localStorage.removeItem('app_password');
                if (loginErrorHint) loginErrorHint.style.display = 'block';
            }
        } catch (err) {
            console.error('Login validation error:', err);
        }
    }
}

// Check Pipeline Execution Status
async function checkPipelineStatus() {
    try {
        const res = await fetch('/api/status');
        if (!res.ok) return;
        const status = await res.json();
        
        const wasRunning = state.pipelineStatus.is_running;
        state.pipelineStatus = status;

        updateUIStatus();
        
        // Handle transitioning from running to completed
        if (wasRunning && !status.is_running) {
            loadLeads(); // Reload directory
            loadHistory(); // Reload history with new leads
        }
    } catch (err) {
        console.error('Failed to fetch status:', err);
    }
}

// Update UI elements based on state.pipelineStatus
function updateUIStatus() {
    const s = state.pipelineStatus;
    
    // Update stats
    const elapsed = s.elapsed_seconds || 0;
    if (runtimeVal && !s.is_running) {
        runtimeVal.textContent = formatDuration(elapsed);
    }
    if (genRateVal && !s.is_running) {
        if (elapsed > 0) {
            const rate = (s.leads_count / (elapsed / 60)).toFixed(1);
            genRateVal.textContent = `${rate} leads/min`;
        } else if (state.leads && state.leads.length > 0) {
            genRateVal.textContent = `1.2 leads/min`;
        } else {
            genRateVal.textContent = `0.0 leads/min`;
        }
    }
    updateEstimatedReplyRate();

    // Status badges on Header

    if (s.is_running) {
        systemStatusDot.className = 'status-indicator-dot running';
        systemStatusLabel.textContent = s.current_step;
        consolePulse.classList.add('active');
        
        // Disable form inputs
        startBtn.disabled = true;
        startBtn.querySelector('span').textContent = 'Processing...';
        cancelBtn.classList.remove('hidden');
        cancelBtn.disabled = false;
        cancelBtn.querySelector('span').textContent = 'Cancel Run';
        resetBtn.classList.add('hidden');
    } else {
        systemStatusDot.className = 'status-indicator-dot';
        consolePulse.classList.remove('active');
        
        startBtn.disabled = false;
        startBtn.querySelector('span').textContent = 'Produce Leads';
        cancelBtn.classList.add('hidden');
        
        if (s.progress === 100) {
            systemStatusDot.className = 'status-indicator-dot';
            systemStatusLabel.textContent = 'Pipeline Completed';
            resetBtn.classList.remove('hidden');
        } else if (s.error) {
            systemStatusDot.className = 'status-indicator-dot error';
            systemStatusLabel.textContent = 'Error Occurred';
            resetBtn.classList.remove('hidden');
        } else if (s.current_step === 'Cancelled') {
            systemStatusDot.className = 'status-indicator-dot error';
            systemStatusLabel.textContent = 'Run Cancelled';
            resetBtn.classList.remove('hidden');
        } else {
            systemStatusLabel.textContent = 'Pipeline Ready';
            resetBtn.classList.add('hidden');
        }
    }

    // Update Progress indicators
    progressFill.style.width = `${s.progress}%`;
    progressVal.textContent = `${s.progress}%`;

    // Render Logs
    if (s.logs && s.logs.length > 0) {
        // Only re-render if count has changed
        const currentLogCount = consoleLogs.querySelectorAll('.log-line').length;
        if (s.logs.length !== currentLogCount) {
            consoleLogs.innerHTML = '';
            s.logs.forEach(log => {
                const div = document.createElement('div');
                div.className = 'log-line';
                
                // Color formatting codes
                if (log.includes('[OK]')) {
                    div.style.color = '#10b981';
                } else if (log.includes('[FAIL]') || log.includes('[ERROR]')) {
                    div.style.color = '#ef4444';
                } else if (log.includes('[MEMORY]')) {
                    div.style.color = '#a78bfa';
                } else if (log.includes('================')) {
                    div.style.color = '#6366f1';
                }
                
                div.textContent = log;
                consoleLogs.appendChild(div);
            });
            // Auto scroll console
            consoleLogs.scrollTop = consoleLogs.scrollHeight;
        }
    } else if (!s.is_running && s.progress === 0) {
        consoleLogs.innerHTML = `<div class="log-placeholder">Pipeline is currently idle. Configure values above and click "Produce Leads" to start.</div>`;
    }
}

// Load leads from backend
async function loadLeads() {
    try {
        const res = await fetch('/api/leads');
        if (!res.ok) return;
        state.leads = await res.json();
        renderLeadsList();
        updateDownloadButtons();
    } catch (err) {
        console.error('Failed to load leads:', err);
    }
}

// Render list of lead rows
function renderLeadsList() {
    const query = searchInput.value.trim().toLowerCase();
    
    // Filter leads
    const filteredLeads = state.leads.filter(lead => {
        const nameMatch = lead.company_name.toLowerCase().includes(query);
        const taglineMatch = (lead.tagline || '').toLowerCase().includes(query);
        const scoreMatch = String(lead.lead_score || '').includes(query);
        return nameMatch || taglineMatch || scoreMatch;
    });

    leadsCountBadge.textContent = `${filteredLeads.length} Prospects Available`;

    if (filteredLeads.length === 0) {
        leadsList.innerHTML = `
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>
                <h3>No prospects match search</h3>
                <p>Try clearing search keyword or generate new prospects in Dashboard.</p>
            </div>
        `;
        return;
    }

    leadsList.innerHTML = '';
    filteredLeads.forEach(lead => {
        const score = lead.lead_score || 8;
        let scoreClass = 'score-mid';
        if (score >= 9) scoreClass = 'score-high';
        else if (score <= 5) scoreClass = 'score-low';

        const row = document.createElement('div');
        row.className = 'lead-row-card';
        row.innerHTML = `
            <div class="lead-row-left">
                <div class="lead-row-title-bar">
                    <span class="lead-row-title">${escapeHtml(lead.company_name)}</span>
                    <span class="meta-badge">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
                        ${escapeHtml(cleanDomain(lead.email ? lead.email.split('@')[1] : '') || 'website')}
                    </span>
                </div>
                <div class="lead-row-tagline">${escapeHtml(lead.tagline || 'No description listed.')}</div>
            </div>
            <div class="lead-row-right">
                <div class="score-badge-circle ${scoreClass}">${score}</div>
                <button class="btn btn-secondary btn-sm select-lead-btn">View Dossier</button>
            </div>
        `;

        // Click row triggers details tab
        row.querySelector('.select-lead-btn').addEventListener('click', (e) => {
            e.stopPropagation(); // Avoid double trigger
            openLeadDetails(lead);
        });
        row.addEventListener('click', () => {
            openLeadDetails(lead);
        });

        leadsList.appendChild(row);
    });
}

// Load lead history from backend
async function loadHistory() {
    try {
        const res = await fetch('/api/history');
        if (!res.ok) return;
        state.historyLeads = await res.json();
        renderHistoryList();
    } catch (err) {
        console.error('Failed to load lead history:', err);
    }
}

// Render list of history lead rows
function renderHistoryList() {
    if (!historyList) return;
    const query = historySearchInput.value.trim().toLowerCase();
    
    // Filter history leads
    const filteredLeads = state.historyLeads.filter(lead => {
        const nameMatch = lead.company_name.toLowerCase().includes(query);
        const taglineMatch = (lead.tagline || '').toLowerCase().includes(query);
        const scoreMatch = String(lead.lead_score || '').includes(query);
        return nameMatch || taglineMatch || scoreMatch;
    });

    historyCountBadge.textContent = `${filteredLeads.length} Leads in History`;

    if (filteredLeads.length === 0) {
        historyList.innerHTML = `
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                <h3>No history matches search</h3>
                <p>Try clearing your search keyword.</p>
            </div>
        `;
        return;
    }

    historyList.innerHTML = '';
    filteredLeads.forEach(lead => {
        const score = lead.lead_score || 8;
        let scoreClass = 'score-mid';
        if (score >= 9) scoreClass = 'score-high';
        else if (score <= 5) scoreClass = 'score-low';

        const generatedAt = lead.generated_at || '';
        const timestampHtml = generatedAt ? `<span class="meta-badge" style="font-size:0.7rem; opacity:0.7;"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg> ${generatedAt}</span>` : '';

        const row = document.createElement('div');
        row.className = 'lead-row-card';
        row.innerHTML = `
            <div class="lead-row-left">
                <div class="lead-row-title-bar">
                    <span class="lead-row-title">${escapeHtml(lead.company_name)}</span>
                    <span class="meta-badge">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
                        ${escapeHtml(cleanDomain(lead.email ? lead.email.split('@')[1] : '') || 'website')}
                    </span>
                    ${timestampHtml}
                </div>
                <div class="lead-row-tagline">${escapeHtml(lead.tagline || 'No description listed.')}</div>
            </div>
            <div class="lead-row-right">
                <div class="score-badge-circle ${scoreClass}">${score}</div>
                <button class="btn btn-secondary btn-sm select-lead-btn">View Dossier</button>
            </div>
        `;

        // Click row triggers details tab
        row.querySelector('.select-lead-btn').addEventListener('click', (e) => {
            e.stopPropagation(); // Avoid double trigger
            openLeadDetails(lead);
        });
        row.addEventListener('click', () => {
            openLeadDetails(lead);
        });

        historyList.appendChild(row);
    });
}

function cleanDomain(domain) {
    if (!domain) return '';
    return domain.replace('www.', '').toLowerCase();
}

// Show/Hide Download Buttons
function updateDownloadButtons() {
    if (state.leads && state.leads.length > 0) {
        sidebarExports.style.display = 'block';
    } else {
        sidebarExports.style.display = 'none';
    }
}

// Open Details View for a single lead
function openLeadDetails(lead) {
    state.selectedLead = lead;
    
    // Show Details Tab option in sidebar menu (temporarily active)
    detailsMenuBtn.classList.remove('hidden');
    
    // Switch to details tab
    switchTab('details');

    // Score styling
    const score = lead.lead_score || 8;
    let scoreClass = 'score-mid';
    if (score >= 9) scoreClass = 'score-high';
    else if (score <= 5) scoreClass = 'score-low';

    // Parse website URL
    let cleanName = lead.company_name.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
    let websiteUrl = lead.email ? `https://${lead.email.split('@')[1]}` : `https://${cleanName}.com`;

    // Render detailed structure
    let tweetsHtml = '';
    if (lead.recent_tweets && lead.recent_tweets.length > 0) {
        lead.recent_tweets.forEach(t => {
            tweetsHtml += `
                <div class="tweet-card">
                    <div class="tweet-header">
                        <div class="tweet-bird">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/></svg>
                        </div>
                        <span class="tweet-date">${formatDate(t.created_at)}</span>
                    </div>
                    <div class="tweet-text">"${escapeHtml(t.text)}"</div>
                    <div class="tweet-footer">
                        <span class="tweet-stat">💬 Reply</span>
                        <span class="tweet-stat">🔁 ${t.retweets || 0} Retweets</span>
                        <span class="tweet-stat">❤️ ${t.likes || 0} Likes</span>
                    </div>
                </div>
            `;
        });
    } else {
        tweetsHtml = `
            <div class="empty-state" style="padding: 2rem;">
                <p>No recent tweets scraped. Either profile has no activity or Twitter API handle search was skipped.</p>
            </div>
        `;
    }

    leadDetailContent.innerHTML = `
        <!-- HEADER dossier -->
        <div class="lead-detail-header-card">
            <div class="lead-header-info">
                <h2>${escapeHtml(lead.company_name)}</h2>
                <div class="tagline">${escapeHtml(lead.tagline || 'No tagline listed.')}</div>
                <div class="lead-header-meta">
                    <span class="meta-badge">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                        ${escapeHtml(lead.funding || 'Seed Funding')}
                    </span>
                    <span class="meta-badge">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                        HQ: ${escapeHtml(lead.country_based_in || 'United States')}
                    </span>
                </div>
            </div>
            
            <div class="lead-score-detail">
                <div class="score-badge-large ${scoreClass}">${score}</div>
                <div class="score-detail-text">
                    <h4>Qualification Rating</h4>
                    <p>${escapeHtml(lead.score_justification || 'Analyzed matching developer-first ICP target criteria.')}</p>
                </div>
            </div>
        </div>

        <!-- LEFT COLUMN: Details & Pitch -->
        <div class="flex-col">
            <!-- Contact Details -->
            <div class="card p-xl">
                <div class="detail-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                    <span>Target Point of Contact</span>
                </div>
                <div class="detail-grid">
                    <div class="detail-field">
                        <label>Decision Maker</label>
                        <span class="value">${escapeHtml(lead.contact_name || 'Not found')}</span>
                    </div>
                    <div class="detail-field">
                        <label>Job Title</label>
                        <span class="value">${escapeHtml(lead.contact_title || 'Founder / CTO')}</span>
                    </div>
                    <div class="detail-field">
                        <label>Email Address</label>
                        <a href="mailto:${escapeHtml(lead.email)}" class="value">${escapeHtml(lead.email || 'Not found')}</a>
                    </div>
                    <div class="detail-field">
                        <label>Phone Number</label>
                        <span class="value">${escapeHtml(lead.phone || 'Not found')}</span>
                    </div>
                    <div class="detail-field">
                        <label>LinkedIn Dossier</label>
                        ${lead.linkedin !== 'Not listed' ? `<a href="${escapeHtml(lead.linkedin.startsWith('http') ? lead.linkedin : 'https://' + lead.linkedin)}" target="_blank" class="value">Open LinkedIn Profile ↗</a>` : '<span class="value text-muted">Not listed</span>'}
                    </div>
                    <div class="detail-field">
                        <label>X / Twitter</label>
                        ${lead.twitter !== 'Not listed' ? `<a href="${escapeHtml(lead.twitter.startsWith('http') ? lead.twitter : 'https://' + lead.twitter)}" target="_blank" class="value">Open Profile ↗</a>` : '<span class="value text-muted">Not listed</span>'}
                    </div>
                </div>
            </div>

            <!-- Strategy & Personalized Angle -->
            <div class="card p-xl">
                <div class="detail-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2V2z"></polygon><path d="M2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>
                    <span>Outreach & Package Strategy</span>
                </div>
                <div class="detail-field">
                    <label>Recommended Sponsorship Package</label>
                    <span class="value" style="font-size: 1.1rem; color: var(--primary); font-weight: 700;">${escapeHtml(lead.recommended_package || 'Newsletter ad ($199)')}</span>
                </div>
                
                <div class="pitch-block">
                    <h4>Why This Company is a Fit</h4>
                    <p>${escapeHtml(lead.why_pitch_fits || 'No fit reasoning generated.')}</p>
                </div>
                
                <div class="outreach-angle-box">
                    <h4>Tailored Outreach Hook</h4>
                    <p>"${escapeHtml(lead.tailored_outreach_angle || 'Hi there, noticed what you are building.')}"</p>
                </div>
            </div>
        </div>

        <!-- RIGHT COLUMN: Firmographics & Twitter -->
        <div class="flex-col">
            <!-- Company Intel -->
            <div class="card p-xl">
                <div class="detail-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                    <span>Firmographic Context</span>
                </div>
                <div class="detail-field" style="margin-bottom: 1rem;">
                    <label>Funding Status</label>
                    <span class="value">${escapeHtml(lead.funding || 'Unknown / Self-funded')}</span>
                </div>
                <div class="detail-field">
                    <label>Executive / Founder Background</label>
                    <span class="value" style="font-size: 0.9rem; line-height: 1.4;">${escapeHtml(lead.background_of_founders || 'Background not available.')}</span>
                </div>
            </div>

            <!-- Scraped Twitter Activity -->
            <div class="card p-xl">
                <div class="detail-section-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"></path></svg>
                    <span>Scraped Recent Tweets (apidojo/tweet-scraper)</span>
                </div>
                <div class="tweets-feed">
                    ${tweetsHtml}
                </div>
            </div>
        </div>
    `;
}

function formatDate(dateStr) {
    if (!dateStr) return 'Just now';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
        return dateStr;
    }
}

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// Check local credentials
// Check local credentials
async function checkApiCredentials() {
    try {
        const res = await fetch('/api/config');
        if (!res.ok) return;
        const cfg = await res.json();

        updateBadge('status-openai', cfg.openai);
        updateBadge('status-apify', cfg.apify);
        updateBadge('status-firecrawl', cfg.firecrawl);
        updateBadge('status-smtp', cfg.smtp);
        
        loadApiUsage(cfg);
    } catch (err) {
        console.error('Failed to get credentials config:', err);
    }
}

function updateBadge(id, isConnected) {
    const el = document.getElementById(id);
    if (!el) return;
    if (isConnected) {
        el.className = 'api-badge connected';
        el.textContent = 'Active / Connected';
    } else {
        el.className = 'api-badge missing';
        el.textContent = 'Missing Key';
    }
}

// Fetch and load quota/usage limits in settings
async function loadApiUsage(cfg) {
    const usageList = document.getElementById('usage-list');
    if (!usageList) return;
    
    usageList.innerHTML = '<div class="usage-loading">Fetching current API usage limits...</div>';
    
    try {
        const res = await fetch('/api/usage');
        if (!res.ok) {
            usageList.innerHTML = '<div class="usage-loading text-danger">Failed to fetch usage limits.</div>';
            return;
        }
        const usage = await res.json();
        
        let html = '';
        
        // 1. OpenAI Usage
        if (cfg.openai) {
            const openAIUsage = usage.openai;
            if (openAIUsage.status === 'Active') {
                html += `
                    <div class="usage-status-item">
                        <div class="usage-header">
                            <span class="usage-title">🟢 OpenAI API Key</span>
                            <span class="usage-value-text">Active</span>
                        </div>
                        <div class="progress-bar-bg" style="background-color: rgba(16, 185, 129, 0.2); width: 100%; border-radius: 6px; height: 10px; overflow: hidden;">
                            <div class="progress-bar-fill" style="width: 100%; background-color: var(--success); height: 100%;"></div>
                        </div>
                        <span class="usage-info">${openAIUsage.message}</span>
                    </div>
                `;
            } else if (openAIUsage.status === 'Success') {
                html += `
                    <div class="usage-status-item">
                        <div class="usage-header">
                            <span class="usage-title">🟢 OpenAI Admin API Key</span>
                            <span class="usage-value-text">Active (Costs Enabled)</span>
                        </div>
                        <div class="progress-bar-bg" style="background-color: rgba(16, 185, 129, 0.2); width: 100%; border-radius: 6px; height: 10px; overflow: hidden;">
                            <div class="progress-bar-fill" style="width: 100%; background-color: var(--success); height: 100%;"></div>
                        </div>
                        <span class="usage-info">Organization costs and token limits are actively tracked.</span>
                    </div>
                `;
            } else {
                html += `
                    <div class="usage-status-item">
                        <div class="usage-header">
                            <span class="usage-title">🔴 OpenAI API Key</span>
                            <span class="usage-value-text">Offline / Error</span>
                        </div>
                        <span class="usage-info">Error details: ${openAIUsage.message || 'Verification failed.'}</span>
                    </div>
                `;
            }
        }
        
        // 2. Apify Usage
        if (cfg.apify) {
            const apifyUsage = usage.apify;
            if (apifyUsage.status === 'Success') {
                const limit = apifyUsage.limit_usd;
                const used = apifyUsage.usage_usd;
                const pct = limit > 0 ? Math.min(100, (used / limit) * 100) : 0;
                const remaining = apifyUsage.remaining_usd;
                
                html += `
                    <div class="usage-status-item">
                        <div class="usage-header">
                            <span class="usage-title">🟢 Apify Account (${escapeHtml(apifyUsage.username)})</span>
                            <span class="usage-value-text">$${used.toFixed(2)} / $${limit.toFixed(2)} USD</span>
                        </div>
                        <div class="progress-bar-bg" style="background-color: var(--border-color); width: 100%; border-radius: 6px; height: 10px; overflow: hidden;">
                            <div class="progress-bar-fill" style="width: ${pct}%; background-color: ${pct > 80 ? 'var(--danger)' : 'var(--primary)'}; height: 100%; transition: width 0.4s ease;"></div>
                        </div>
                        <span class="usage-info">$${remaining.toFixed(2)} USD remaining in current billing cycle.</span>
                    </div>
                `;
            } else {
                html += `
                    <div class="usage-status-item">
                        <div class="usage-header">
                            <span class="usage-title">🔴 Apify Account Usage</span>
                            <span class="usage-value-text">Error checking usage</span>
                        </div>
                        <span class="usage-info">Error details: ${escapeHtml(apifyUsage.message || 'Connection failed.')}</span>
                    </div>
                `;
            }
        }
        
        // 3. Firecrawl Usage
        if (cfg.firecrawl) {
            const firecrawlUsage = usage.firecrawl;
            if (firecrawlUsage.status === 'Success') {
                const total = firecrawlUsage.total_credits;
                const remaining = firecrawlUsage.remaining_credits;
                const used = firecrawlUsage.used_credits;
                const pct = total > 0 ? Math.min(100, (used / total) * 100) : 0;
                
                html += `
                    <div class="usage-status-item">
                        <div class="usage-header">
                            <span class="usage-title">🟢 Firecrawl Credits</span>
                            <span class="usage-value-text">${remaining} / ${total} remaining</span>
                        </div>
                        <div class="progress-bar-bg" style="background-color: var(--border-color); width: 100%; border-radius: 6px; height: 10px; overflow: hidden;">
                            <div class="progress-bar-fill" style="width: ${100 - pct}%; background-color: var(--success); height: 100%; transition: width 0.4s ease;"></div>
                        </div>
                        <span class="usage-info">${used} credits used. Credits reset monthly.</span>
                    </div>
                `;
            } else {
                html += `
                    <div class="usage-status-item">
                        <div class="usage-header">
                            <span class="usage-title">🔴 Firecrawl Account Usage</span>
                            <span class="usage-value-text">Error checking usage</span>
                        </div>
                        <span class="usage-info">Error details: ${escapeHtml(firecrawlUsage.message || 'Connection failed.')}</span>
                    </div>
                `;
            }
        }
        
        if (!html) {
            html = '<div class="usage-loading">No active API keys found. Configure keys in your <code>.env</code> file.</div>';
        }
        
        usageList.innerHTML = html;
    } catch (err) {
        console.error('Failed to load usage details:', err);
        usageList.innerHTML = '<div class="usage-loading text-danger">Error loading usage info.</div>';
    }
}

// Utility Functions for Stats
function formatDuration(sec) {
    if (sec < 0) sec = 0;
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${String(m).padStart(2, '0')}m ${String(s).padStart(2, '0')}s`;
}

function updateRuntimeCounter() {
    const s = state.pipelineStatus;
    if (s && s.is_running && s.start_time) {
        const elapsed = Math.max(0, Math.floor(Date.now() / 1000) - s.start_time);
        if (runtimeVal) runtimeVal.textContent = formatDuration(elapsed);
        
        if (genRateVal && elapsed > 0) {
            const rate = (s.leads_count / (elapsed / 60)).toFixed(1);
            genRateVal.textContent = `${rate} leads/min`;
        }
    }
}

function updateEstimatedReplyRate() {
    const s = state.pipelineStatus;
    let scores = [];
    if (s && s.is_running && s.lead_scores && s.lead_scores.length > 0) {
        scores = s.lead_scores;
    } else if (state.leads && state.leads.length > 0) {
        scores = state.leads.map(l => l.lead_score).filter(Boolean);
    }
    
    const avgScore = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length) : 8.0;
    const replyRate = (avgScore * 2.5 + 5.0).toFixed(1);
    
    if (replyRateVal) replyRateVal.textContent = `${replyRate}%`;
    if (replyRateBar) replyRateBar.style.width = `${replyRate}%`;
}

