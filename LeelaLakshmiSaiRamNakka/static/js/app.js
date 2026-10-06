// AI Support Desk - shared front-end behavior

// ---- Theme (persisted in localStorage; this is a real deployed site, not a sandboxed artifact) ----
(function initTheme() {
    const stored = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (stored === 'dark' || (!stored && prefersDark)) {
        document.documentElement.classList.add('dark');
    }
})();

function toggleTheme() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// ---- Sidebar (mobile) ----
function initSidebar() {
    const sidebar = document.getElementById('sidebar-nav');
    const openBtn = document.getElementById('sidebar-toggle');
    const collapseBtn = document.getElementById('sidebar-collapse');
    const closeBtn = document.getElementById('sidebar-close');
    const overlay = document.getElementById('sidebar-overlay');
    if (!sidebar) return;

    const open = () => {
        sidebar.classList.remove('sidebar-collapsed', '-translate-x-full');
        overlay?.classList.remove('hidden');
        document.body.classList.remove('sidebar-collapsed');
    };
    const close = () => {
        sidebar.classList.add('sidebar-collapsed', '-translate-x-full');
        overlay?.classList.add('hidden');
        document.body.classList.add('sidebar-collapsed');
    };

    const toggle = () => {
        if (sidebar.classList.contains('sidebar-collapsed')) {
            open();
        } else {
            close();
        }
    };

    openBtn?.addEventListener('click', toggle);
    collapseBtn?.addEventListener('click', close);
    closeBtn?.addEventListener('click', close);
    overlay?.addEventListener('click', close);
}

// ---- Toasts ----
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) { return; }
    const colors = {
        success: 'bg-emerald-600',
        error: 'bg-rose-600',
        info: 'bg-slate-800 dark:bg-slate-700'
    };
    const icons = {
        success: 'fa-circle-check',
        error: 'fa-circle-exclamation',
        info: 'fa-circle-info'
    };
    const toast = document.createElement('div');
    toast.className = `fade-in ${colors[type] || colors.info} text-white text-xs font-semibold px-4 py-3 rounded-xl shadow-lg flex items-center gap-2 max-w-xs`;
    toast.innerHTML = `<i class="fa-solid ${icons[type] || icons.info}"></i><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.transition = 'opacity .25s ease';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 250);
    }, 3500);
}

// ---- Auth-aware fetch: sends the session cookie, and bounces to login on 401 ----
async function apiFetch(url, options = {}) {
    const response = await fetch(url, {
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
        ...options
    });
    if (response.status === 401) {
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }
    return response;
}

async function handleLogout() {
    try {
        await apiFetch('/api/auth/logout', { method: 'POST' });
    } finally {
        window.location.href = '/login';
    }
}

document.addEventListener('DOMContentLoaded', initSidebar);
