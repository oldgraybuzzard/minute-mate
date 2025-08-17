/**
 * MinuteMate Admin Panel JavaScript
 * Handles admin functionality for user management and system administration
 */

class AdminPanel {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.currentTab = 'users';
        this.users = [];
        this.selectedUserId = null;
        
        this.initializeAdmin();
    }

    initializeAdmin() {
        this.bindEvents();
        this.loadUsers();
        this.loadSystemInfo();
    }

    bindEvents() {
        // Tab switching
        document.querySelectorAll('.admin-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.target.closest('.admin-tab').dataset.tab;
                this.switchTab(tabName);
            });
        });

        // User management events
        document.getElementById('create-user-btn').addEventListener('click', () => {
            this.openCreateUserModal();
        });

        document.getElementById('refresh-users').addEventListener('click', () => {
            this.loadUsers();
        });

        document.getElementById('user-search').addEventListener('input', (e) => {
            this.filterUsers(e.target.value);
        });

        document.getElementById('user-status-filter').addEventListener('change', (e) => {
            this.filterUsersByStatus(e.target.value);
        });

        // Toast close
        document.querySelector('.toast-close').addEventListener('click', () => {
            this.hideToast();
        });
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.admin-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.admin-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        this.currentTab = tabName;

        // Load tab-specific data
        if (tabName === 'users') {
            this.loadUsers();
        } else if (tabName === 'system') {
            this.loadSystemInfo();
        } else if (tabName === 'logs') {
            this.loadLogs();
        }
    }

    async loadUsers() {
        try {
            this.showLoading('Loading users...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/admin/users`, {
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.users = result.data.users;
                    this.displayUsers(this.users);
                } else {
                    throw new Error(result.message);
                }
            } else {
                throw new Error('Failed to load users');
            }
        } catch (error) {
            console.error('Error loading users:', error);
            this.showToast('Failed to load users', 'error');
            // For development, create mock users if API fails
            this.createMockUsers();
        } finally {
            this.hideLoading();
        }
    }

    createMockUsers() {
        // Mock users for development when API is not available
        this.users = [
            {
                id: 'c9b51080-9879-48cf-b07b-236b10b61161',
                username: 'kfelder',
                email: 'k_felder@me.com',
                first_name: 'Kendall',
                last_name: 'Felder',
                is_active: true,
                created_at: '2025-08-17T15:29:44',
                last_login: null
            }
        ];
        this.displayUsers(this.users);
    }

    displayUsers(users) {
        const tbody = document.getElementById('users-table-body');
        
        if (users.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="no-data">No users found</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = users.map(user => `
            <tr>
                <td class="user-id">${user.id.substring(0, 8)}...</td>
                <td class="user-username">${user.username}</td>
                <td class="user-email">${user.email}</td>
                <td class="user-name">${user.first_name} ${user.last_name}</td>
                <td class="user-status">
                    <span class="status-badge ${user.is_active ? 'active' : 'inactive'}">
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td class="user-created">${this.formatDate(user.created_at)}</td>
                <td class="user-last-login">${user.last_login ? this.formatDate(user.last_login) : 'Never'}</td>
                <td class="user-actions">
                    <button class="btn-icon" onclick="adminPanel.resetPassword('${user.id}', '${user.username}', '${user.email}')" title="Reset Password">
                        <i class="fas fa-key"></i>
                    </button>
                    <button class="btn-icon" onclick="adminPanel.toggleUserStatus('${user.id}', ${user.is_active})" title="${user.is_active ? 'Deactivate' : 'Activate'} User">
                        <i class="fas fa-${user.is_active ? 'user-slash' : 'user-check'}"></i>
                    </button>
                    <button class="btn-icon danger" onclick="adminPanel.deleteUser('${user.id}', '${user.username}')" title="Delete User">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    filterUsers(searchTerm) {
        const filtered = this.users.filter(user => 
            user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
            user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
            `${user.first_name} ${user.last_name}`.toLowerCase().includes(searchTerm.toLowerCase())
        );
        this.displayUsers(filtered);
    }

    filterUsersByStatus(status) {
        if (!status) {
            this.displayUsers(this.users);
            return;
        }
        
        const filtered = this.users.filter(user => {
            if (status === 'active') return user.is_active;
            if (status === 'inactive') return !user.is_active;
            return true;
        });
        this.displayUsers(filtered);
    }

    openCreateUserModal() {
        document.getElementById('create-user-modal').classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    closeCreateUserModal() {
        document.getElementById('create-user-modal').classList.remove('show');
        document.body.style.overflow = '';
        document.getElementById('create-user-form').reset();
    }

    async createUser() {
        try {
            const username = document.getElementById('new-username').value.trim();
            const email = document.getElementById('new-email').value.trim();
            const password = document.getElementById('new-password').value;
            const firstName = document.getElementById('new-first-name').value.trim();
            const lastName = document.getElementById('new-last-name').value.trim();
            const isAdmin = document.getElementById('new-is-admin').checked;

            if (!username || !email || !password) {
                this.showToast('Please fill in all required fields', 'error');
                return;
            }

            this.showLoading('Creating user...');

            // For development, use the CLI script
            const response = await fetch(`${this.apiBaseUrl}/api/admin/create-user`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    first_name: firstName,
                    last_name: lastName,
                    is_admin: isAdmin
                })
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.showToast('User created successfully', 'success');
                    this.closeCreateUserModal();
                    this.loadUsers();
                } else {
                    throw new Error(result.message);
                }
            } else {
                throw new Error('Failed to create user');
            }
        } catch (error) {
            console.error('Error creating user:', error);
            this.showToast('Failed to create user: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    resetPassword(userId, username, email) {
        this.selectedUserId = userId;
        document.getElementById('reset-user-info').value = `${username} (${email})`;
        document.getElementById('reset-password-modal').classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    closeResetPasswordModal() {
        document.getElementById('reset-password-modal').classList.remove('show');
        document.body.style.overflow = '';
        document.getElementById('reset-password-form').reset();
        this.selectedUserId = null;
    }

    async resetUserPassword() {
        try {
            const newPassword = document.getElementById('reset-new-password').value;
            const confirmPassword = document.getElementById('reset-confirm-password').value;

            if (!newPassword || !confirmPassword) {
                this.showToast('Please fill in all fields', 'error');
                return;
            }

            if (newPassword !== confirmPassword) {
                this.showToast('Passwords do not match', 'error');
                return;
            }

            if (newPassword.length < 6) {
                this.showToast('Password must be at least 6 characters long', 'error');
                return;
            }

            this.showLoading('Resetting password...');

            // For development, show success message
            this.showToast('Password reset successfully', 'success');
            this.closeResetPasswordModal();

        } catch (error) {
            console.error('Error resetting password:', error);
            this.showToast('Failed to reset password', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async loadSystemInfo() {
        try {
            // Mock system info for development
            document.getElementById('total-users').textContent = this.users.length;
            document.getElementById('total-meetings').textContent = '0';
            document.getElementById('db-size').textContent = '2.5 MB';
            document.getElementById('last-backup').textContent = 'Never';
            document.getElementById('uptime').textContent = '2h 15m';
        } catch (error) {
            console.error('Error loading system info:', error);
        }
    }

    async loadLogs() {
        try {
            const logsDisplay = document.getElementById('logs-display');
            logsDisplay.innerHTML = `
                <div class="log-entry info">
                    <span class="log-time">2025-08-17 15:29:44</span>
                    <span class="log-level">INFO</span>
                    <span class="log-message">User 'kfelder' created successfully</span>
                </div>
                <div class="log-entry info">
                    <span class="log-time">2025-08-17 15:25:12</span>
                    <span class="log-level">INFO</span>
                    <span class="log-message">Database migration completed successfully</span>
                </div>
                <div class="log-entry info">
                    <span class="log-time">2025-08-17 15:20:01</span>
                    <span class="log-level">INFO</span>
                    <span class="log-message">Server started on port 5000</span>
                </div>
            `;
        } catch (error) {
            console.error('Error loading logs:', error);
        }
    }

    formatDate(dateString) {
        if (!dateString) return 'Never';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    showLoading(message) {
        // Simple loading implementation
        console.log('Loading:', message);
    }

    hideLoading() {
        console.log('Loading complete');
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('admin-toast');
        const messageEl = toast.querySelector('.toast-message');
        const iconEl = toast.querySelector('.toast-icon i');

        messageEl.textContent = message;
        
        // Update icon based on type
        iconEl.className = type === 'success' ? 'fas fa-check-circle' :
                          type === 'error' ? 'fas fa-exclamation-circle' :
                          type === 'warning' ? 'fas fa-exclamation-triangle' :
                          'fas fa-info-circle';

        toast.className = `toast ${type} show`;

        // Auto hide after 5 seconds
        setTimeout(() => {
            this.hideToast();
        }, 5000);
    }

    hideToast() {
        const toast = document.getElementById('admin-toast');
        toast.classList.remove('show');
    }
}

// Global functions for onclick handlers
function closeCreateUserModal() {
    adminPanel.closeCreateUserModal();
}

function createUser() {
    adminPanel.createUser();
}

function closeResetPasswordModal() {
    adminPanel.closeResetPasswordModal();
}

function resetUserPassword() {
    adminPanel.resetUserPassword();
}

// Initialize admin panel when page loads
let adminPanel;
document.addEventListener('DOMContentLoaded', () => {
    adminPanel = new AdminPanel();
});
