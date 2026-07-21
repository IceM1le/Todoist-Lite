// ----- Constants -----
const API_BASE = '';
let currentPage = 1;
const limit = 15;

// ----- Theme -----
function getTheme() {
    return localStorage.getItem('theme') || 'light';
}
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    const toggle = document.getElementById('theme-toggle');
    if (toggle) toggle.textContent = theme === 'dark' ? '☀️' : '🌙';
}
function toggleTheme() {
    const current = getTheme();
    setTheme(current === 'dark' ? 'light' : 'dark');
}

// ----- Toast -----
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ----- Auth -----
function getToken() { return localStorage.getItem('access_token'); }
function setToken(token) { localStorage.setItem('access_token', token); }
function removeToken() { localStorage.removeItem('access_token'); }
function isAuthenticated() { return !!getToken(); }

// ----- API -----
async function apiRequest(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const resp = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    if (resp.status === 401) {
        removeToken();
        window.location.href = '/login';
        return null;
    }
    return resp;
}

// ----- Load tasks -----
async function loadTasks() {
    if (!isAuthenticated()) { window.location.href = '/login'; return; }

    const search = document.getElementById('search')?.value || '';
    const isDone = document.getElementById('filter-status')?.value || '';
    const priority = document.getElementById('filter-priority')?.value || '';
    const sortBy = document.getElementById('sort-by')?.value || 'id';
    const sortOrder = document.getElementById('sort-order')?.value || 'asc';

    let url = `/tasks?page=${currentPage}&limit=${limit}&sort_by=${sortBy}&order=${sortOrder}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (isDone) url += `&is_done=${isDone}`;
    if (priority) url += `&priority=${priority}`;

    const resp = await apiRequest(url);
    if (!resp) return;
    if (!resp.ok) {
        showToast('Failed to load tasks', 'error');
        return;
    }
    const data = await resp.json();
    renderTasks(data.items);
    updatePagination(data.page, data.pages);
}

// ----- Render tasks (with time left) -----
function renderTasks(tasks) {
    const container = document.getElementById('tasks-container');
    if (!container) return;
    if (!tasks || tasks.length === 0) {
        container.innerHTML = `<p style="text-align:center;color:var(--text-muted);padding:40px 0;">✨ No tasks yet. Create one!</p>`;
        return;
    }
    container.innerHTML = tasks.map(task => {
        const timeLeftHtml = getTimeLeftHtml(task.due_date, task.is_done);
        const doneClass = task.is_done ? 'done' : '';
        return `
        <div class="task-card ${doneClass}" data-id="${task.id}">
            <input type="checkbox" class="toggle-done" ${task.is_done ? 'checked' : ''}>
            <div class="task-info">
                <span class="task-title">${escapeHtml(task.title)}</span>
                <div class="task-meta">
                    <span>🔹 ${task.priority}</span>
                    <span>📅 ${task.due_date ? new Date(task.due_date).toLocaleDateString() : '—'}</span>
                    ${timeLeftHtml}
                    <span>${task.is_done ? '✅ Done' : '⏳ Active'}</span>
                </div>
            </div>
            <div class="task-actions">
                <button class="edit-btn" title="Edit">✏️</button>
                <button class="delete-btn" title="Delete">🗑️</button>
            </div>
        </div>`;
    }).join('');

    container.querySelectorAll('.task-card').forEach(card => {
        const id = parseInt(card.dataset.id);
        const checkbox = card.querySelector('.toggle-done');
        if (checkbox) {
            checkbox.addEventListener('change', (e) => toggleTask(id, e.target.checked));
        }
        card.querySelector('.edit-btn')?.addEventListener('click', () => openEditModal(id));
        card.querySelector('.delete-btn')?.addEventListener('click', () => deleteTask(id));
    });
}

// ----- Time left helper -----
function getTimeLeftHtml(dueDate, isDone) {
    if (isDone) return ''; // выполненные задачи не показывают таймер
    if (!dueDate) return '<span class="time-left">No due date</span>';
    const now = new Date();
    const due = new Date(dueDate);
    const diff = due - now;
    if (diff < 0) {
        const hours = Math.floor(Math.abs(diff) / (1000 * 60 * 60));
        return `<span class="time-left overdue">⏰ Overdue by ${hours}h</span>`;
    }
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    if (days > 0) {
        if (days > 7) return `<span class="time-left">📅 ${days} days left</span>`;
        else return `<span class="time-left soon">⏳ ${days} days left</span>`;
    }
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours > 0) return `<span class="time-left soon">⏳ ${hours}h left</span>`;
    const minutes = Math.floor(diff / (1000 * 60));
    if (minutes > 0) return `<span class="time-left soon">⏳ ${minutes}m left</span>`;
    return `<span class="time-left soon">⏳ Less than a minute</span>`;
}

// ----- Pagination -----
function updatePagination(page, pages) {
    document.getElementById('page-info').textContent = `Page ${page} of ${pages || 1}`;
    document.getElementById('prev-page').disabled = page <= 1;
    document.getElementById('next-page').disabled = page >= pages;
}

// ----- CRUD -----
async function createTask(data) {
    const resp = await apiRequest('/tasks', { method: 'POST', body: JSON.stringify(data) });
    if (resp && resp.ok) {
        showToast('Task created!', 'success');
        loadTasks();
        closeModal();
        return true;
    } else if (resp) {
        const err = await resp.json();
        showToast(err.detail || 'Error creating task', 'error');
        return false;
    }
}
async function updateTask(id, data) {
    const resp = await apiRequest(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
    if (resp && resp.ok) {
        showToast('Task updated', 'success');
        loadTasks();
        closeModal();
        return true;
    } else if (resp) {
        const err = await resp.json();
        showToast(err.detail || 'Error updating task', 'error');
        return false;
    }
}
async function deleteTask(id) {
    if (!confirm('Delete this task?')) return;
    const resp = await apiRequest(`/tasks/${id}`, { method: 'DELETE' });
    if (resp && resp.ok) {
        showToast('Task deleted', 'success');
        loadTasks();
    } else {
        showToast('Failed to delete task', 'error');
    }
}
async function toggleTask(id, isDone) {
    await updateTask(id, { is_done: isDone });
}

// ----- Modal -----
function openModal(title, taskData = null) {
    const modal = document.getElementById('task-modal');
    if (!modal) return;
    modal.classList.add('active');
    document.getElementById('modal-title').textContent = title;
    if (taskData) {
        document.getElementById('task-id').value = taskData.id;
        document.getElementById('task-title').value = taskData.title;
        document.getElementById('task-description').value = taskData.description || '';
        document.getElementById('task-priority').value = taskData.priority || 2;
        document.getElementById('task-is-done').checked = taskData.is_done || false;
        if (taskData.due_date) {
            const dt = new Date(taskData.due_date);
            document.getElementById('task-due-date').value = dt.toISOString().slice(0, 16);
        } else {
            document.getElementById('task-due-date').value = '';
        }
    } else {
        document.getElementById('task-id').value = '';
        document.getElementById('task-title').value = '';
        document.getElementById('task-description').value = '';
        document.getElementById('task-priority').value = 2;
        document.getElementById('task-is-done').checked = false;
        document.getElementById('task-due-date').value = '';
    }
}
function closeModal() {
    const modal = document.getElementById('task-modal');
    if (modal) modal.classList.remove('active');
}
function openEditModal(id) {
    apiRequest(`/tasks/${id}`).then(resp => {
        if (resp && resp.ok) {
            resp.json().then(data => openModal('Edit Task', data));
        }
    });
}

// ----- Logout -----
function logout() {
    removeToken();
    window.location.href = '/login';
}

// ----- Settings (Profile) -----
async function loadProfile() {
    const resp = await apiRequest('/auth/me');
    if (resp && resp.ok) {
        const data = await resp.json();
        document.getElementById('settings-username').value = data.name || '';
        document.getElementById('settings-email').value = data.email || '';
        document.getElementById('settings-telegram-id').value = data.telegram_chat_id || '';
    }
}

async function saveProfile(telegramChatId) {
    const resp = await apiRequest('/auth/me', {
        method: 'PATCH',
        body: JSON.stringify({ telegram_chat_id: telegramChatId || null })
    });
    if (resp && resp.ok) {
        showToast('Профиль обновлён!', 'success');
        closeSettingsModal();
        return true;
    } else if (resp) {
        const err = await resp.json();
        showToast(err.detail || 'Ошибка обновления', 'error');
        return false;
    }
}

function openSettingsModal() {
    document.getElementById('settings-modal').classList.add('active');
    loadProfile();
}

function closeSettingsModal() {
    document.getElementById('settings-modal').classList.remove('active');
}

// ----- Escape helper -----
function escapeHtml(unsafe) {
    return unsafe.replace(/[&<>"]/g, m => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[m] || m));
}

// ----- DOM ready -----
document.addEventListener('DOMContentLoaded', () => {
    // Theme
    setTheme(getTheme());
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);

    // Registration
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const resp = await fetch('/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password }),
            });
            if (resp.ok) {
                window.location.href = '/login';
            } else {
                const err = await resp.json();
                document.getElementById('error-message').textContent = err.detail || 'Registration error';
            }
        });
    }

    // Login
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);
            const resp = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData,
            });
            if (resp.ok) {
                const data = await resp.json();
                setToken(data.access_token);
                window.location.href = '/';
            } else {
                const err = await resp.json();
                document.getElementById('error-message').textContent = err.detail || 'Invalid credentials';
            }
        });
    }

    // Logout
    document.getElementById('logout-btn')?.addEventListener('click', logout);

    // Filters
    document.getElementById('apply-filters')?.addEventListener('click', () => {
        currentPage = 1;
        loadTasks();
    });

    // Pagination
    document.getElementById('prev-page')?.addEventListener('click', () => {
        if (currentPage > 1) { currentPage--; loadTasks(); }
    });
    document.getElementById('next-page')?.addEventListener('click', () => {
        currentPage++; loadTasks();
    });

    // Modal controls for tasks
    document.getElementById('create-task-btn')?.addEventListener('click', () => openModal('New Task'));
    const closeBtn = document.querySelector('.close-btn');
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    const modal = document.getElementById('task-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) closeModal();
        });
    }

    // Task form
    document.getElementById('task-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('task-id').value;
        const title = document.getElementById('task-title').value.trim();
        const description = document.getElementById('task-description').value.trim();
        const priority = parseInt(document.getElementById('task-priority').value) || 2;
        const is_done = document.getElementById('task-is-done').checked;
        const due_date = document.getElementById('task-due-date').value;
        const data = { title, description, priority, is_done };
        if (due_date) data.due_date = new Date(due_date).toISOString();
        if (id) {
            await updateTask(parseInt(id), data);
        } else {
            await createTask(data);
        }
    });

    // Settings button and modal
    document.getElementById('settings-btn')?.addEventListener('click', openSettingsModal);
    document.getElementById('settings-close')?.addEventListener('click', closeSettingsModal);
    document.getElementById('settings-modal')?.addEventListener('click', (e) => {
        if (e.target === e.currentTarget) closeSettingsModal();
    });
    document.getElementById('how-to-get-id')?.addEventListener('click', () => {
        const inst = document.getElementById('telegram-instruction');
        inst.style.display = inst.style.display === 'none' ? 'block' : 'none';
    });
    document.getElementById('settings-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const chatId = document.getElementById('settings-telegram-id').value.trim();
        await saveProfile(chatId || null);
    });

    // Initial load on main page
    if (document.getElementById('tasks-container')) {
        if (!isAuthenticated()) {
            window.location.href = '/login';
        } else {
            loadTasks();
        }
    }
        // ===== Settings (Profile) =====
    async function loadProfile() {
        const resp = await apiRequest('/auth/me');
        if (resp && resp.ok) {
            const data = await resp.json();
            document.getElementById('settings-username').value = data.name || '';
            document.getElementById('settings-email').value = data.email || '';
            document.getElementById('settings-telegram-id').value = data.telegram_chat_id || '';
        }
    }

    // Инициализация обработчиков
    document.addEventListener('DOMContentLoaded', function() {
        document.getElementById('settings-btn')?.addEventListener('click', openSettingsModal);
        document.getElementById('settings-close')?.addEventListener('click', closeSettingsModal);
        document.getElementById('settings-modal')?.addEventListener('click', function(e) {
            if (e.target === e.currentTarget) closeSettingsModal();
        });
        document.getElementById('how-to-get-id')?.addEventListener('click', function() {
            const inst = document.getElementById('telegram-instruction');
            inst.style.display = inst.style.display === 'none' ? 'block' : 'none';
        });
        document.getElementById('settings-form')?.addEventListener('submit', async function(e) {
            e.preventDefault();
            const chatId = document.getElementById('settings-telegram-id').value.trim();
            await saveProfile(chatId || null);
        });
    });
});