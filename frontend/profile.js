/**
 * MinuteMate Profile & Settings JavaScript
 * Handles user profile management and application settings
 */

class ProfileApp {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.currentUser = null;
        this.currentTab = 'profile';
        
        this.initializeElements();
        this.setupEventListeners();
        this.initializeTheme();
        this.checkAuthentication();
    }

    initializeElements() {
        // User elements
        this.userMenuToggle = document.getElementById('user-menu-toggle');
        this.userDropdown = document.getElementById('user-dropdown');
        this.userName = document.getElementById('user-name');
        this.userFullName = document.getElementById('user-full-name');
        this.userEmail = document.getElementById('user-email');
        
        // Tab elements
        this.tabButtons = document.querySelectorAll('.tab-button');
        this.tabPanes = document.querySelectorAll('.tab-pane');
        
        // Form elements
        this.profileForm = document.getElementById('profile-form');
        this.preferencesForm = document.getElementById('preferences-form');
        this.passwordForm = document.getElementById('password-form');
        this.deleteForm = document.getElementById('delete-form');
        
        // Statistics elements
        this.totalMeetings = document.getElementById('total-meetings');
        this.completedMeetings = document.getElementById('completed-meetings');
        this.totalBatches = document.getElementById('total-batches');
        this.successRate = document.getElementById('success-rate');
        
        // Account info elements
        this.accountCreated = document.getElementById('account-created');
        this.lastLogin = document.getElementById('last-login');
        
        // Modal elements
        this.deleteModal = document.getElementById('delete-modal');
        this.exportDataBtn = document.getElementById('export-data-btn');
        this.deleteAccountBtn = document.getElementById('delete-account-btn');
        this.confirmDeleteBtn = document.getElementById('confirm-delete');
        this.cancelDeleteBtn = document.getElementById('cancel-delete');
        
        // UI elements
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.toast = document.getElementById('toast');
        this.themeToggle = document.getElementById('theme-toggle');
    }

    setupEventListeners() {
        // User menu
        this.userMenuToggle.addEventListener('click', () => {
            this.userDropdown.classList.toggle('show');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.userMenuToggle.contains(e.target) && !this.userDropdown.contains(e.target)) {
                this.userDropdown.classList.remove('show');
            }
        });

        // Tab navigation
        this.tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.getAttribute('data-tab');
                this.switchTab(tabName);
            });
        });

        // Form submissions
        this.profileForm.addEventListener('submit', this.updateProfile.bind(this));
        this.preferencesForm.addEventListener('submit', this.updatePreferences.bind(this));
        this.passwordForm.addEventListener('submit', this.changePassword.bind(this));
        this.deleteForm.addEventListener('submit', this.deleteAccount.bind(this));
        
        // Data actions
        this.exportDataBtn.addEventListener('click', this.exportData.bind(this));
        this.deleteAccountBtn.addEventListener('click', () => this.deleteModal.classList.add('show'));
        this.confirmDeleteBtn.addEventListener('click', this.deleteAccount.bind(this));
        this.cancelDeleteBtn.addEventListener('click', () => this.deleteModal.classList.remove('show'));
        
        // Modal close
        this.deleteModal.querySelector('.delete-modal-close').addEventListener('click', () => {
            this.deleteModal.classList.remove('show');
        });
        
        // Close modal when clicking outside
        this.deleteModal.addEventListener('click', (e) => {
            if (e.target === this.deleteModal) {
                this.deleteModal.classList.remove('show');
            }
        });

        // Logout
        document.getElementById('user-logout').addEventListener('click', this.logout.bind(this));
        
        // Theme toggle
        this.themeToggle.addEventListener('click', this.toggleTheme.bind(this));
        
        // Toast close
        this.toast.querySelector('.toast-close').addEventListener('click', () => {
            this.toast.classList.remove('show');
        });
    }

    async checkAuthentication() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/auth/check`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                window.location.href = '/frontend/auth.html';
                return;
            }
            
            const result = await response.json();
            if (!result.success) {
                window.location.href = '/frontend/auth.html';
                return;
            }
            
            this.currentUser = result.data.user;
            this.updateUserInfo();
            this.loadProfile();
            this.loadPreferences();
            
        } catch (error) {
            console.error('Authentication check failed:', error);
            window.location.href = '/frontend/auth.html';
        }
    }

    updateUserInfo() {
        if (this.currentUser) {
            this.userName.textContent = this.currentUser.first_name;
            this.userFullName.textContent = this.currentUser.full_name;
            this.userEmail.textContent = this.currentUser.email;
        }
    }

    async loadProfile() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/profile/`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    const user = result.data.user;
                    this.populateProfileForm(user);
                    this.updateStatistics(user.statistics);
                    this.updateAccountInfo(user);
                }
            }
        } catch (error) {
            console.error('Failed to load profile:', error);
        }
    }

    populateProfileForm(user) {
        document.getElementById('first-name').value = user.first_name || '';
        document.getElementById('last-name').value = user.last_name || '';
        document.getElementById('email').value = user.email || '';
        document.getElementById('timezone').value = user.timezone || 'UTC';
        document.getElementById('language').value = user.language || 'en';
    }

    updateStatistics(stats) {
        if (stats) {
            this.totalMeetings.textContent = stats.total_meetings || 0;
            this.completedMeetings.textContent = stats.completed_meetings || 0;
            this.totalBatches.textContent = stats.total_batches || 0;
            this.successRate.textContent = `${stats.success_rate || 0}%`;
        }
    }

    updateAccountInfo(user) {
        if (user.created_at) {
            this.accountCreated.textContent = new Date(user.created_at).toLocaleDateString();
        }
        if (user.last_login) {
            this.lastLogin.textContent = new Date(user.last_login).toLocaleDateString();
        } else {
            this.lastLogin.textContent = 'Never';
        }
    }

    async loadPreferences() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/profile/preferences`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.populatePreferencesForm(result.data.preferences);
                }
            }
        } catch (error) {
            console.error('Failed to load preferences:', error);
        }
    }

    populatePreferencesForm(preferences) {
        // Theme
        document.getElementById('theme-select').value = preferences.theme || 'light';
        
        // Notifications
        document.getElementById('email-notifications').checked = preferences.notifications?.email_notifications !== false;
        document.getElementById('processing-complete').checked = preferences.notifications?.processing_complete !== false;
        document.getElementById('batch-complete').checked = preferences.notifications?.batch_complete !== false;
        document.getElementById('calendar-sync').checked = preferences.notifications?.calendar_sync !== false;
        
        // Processing
        document.getElementById('default-format').value = preferences.processing?.default_document_format || 'docx';
        document.getElementById('max-file-size').value = preferences.processing?.max_file_size || 100;
        document.getElementById('auto-generate-docs').checked = preferences.processing?.auto_generate_documents !== false;
        document.getElementById('auto-start-batch').checked = preferences.processing?.auto_start_batch === true;
        
        // Privacy
        document.getElementById('data-retention').value = preferences.privacy?.data_retention_days || 365;
        document.getElementById('auto-delete-temp').checked = preferences.privacy?.auto_delete_temp_files !== false;
        document.getElementById('share-analytics').checked = preferences.privacy?.share_analytics === true;
    }

    switchTab(tabName) {
        // Update active tab button
        this.tabButtons.forEach(button => {
            button.classList.remove('active');
            if (button.getAttribute('data-tab') === tabName) {
                button.classList.add('active');
            }
        });
        
        // Update active tab pane
        this.tabPanes.forEach(pane => {
            pane.classList.remove('active');
            if (pane.id === `${tabName}-tab`) {
                pane.classList.add('active');
            }
        });
        
        this.currentTab = tabName;
    }

    async updateProfile(e) {
        e.preventDefault();
        
        try {
            this.showLoading('Updating profile...');
            
            const formData = new FormData(this.profileForm);
            const profileData = Object.fromEntries(formData.entries());
            
            const response = await fetch(`${this.apiBaseUrl}/api/profile/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(profileData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Profile updated successfully', 'success');
                this.currentUser = result.data.user;
                this.updateUserInfo();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Update profile error:', error);
            this.showToast('Failed to update profile', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async updatePreferences(e) {
        e.preventDefault();
        
        try {
            this.showLoading('Updating preferences...');
            
            const formData = new FormData(this.preferencesForm);
            const preferencesData = {
                theme: formData.get('theme'),
                notifications: {
                    email_notifications: document.getElementById('email-notifications').checked,
                    processing_complete: document.getElementById('processing-complete').checked,
                    batch_complete: document.getElementById('batch-complete').checked,
                    calendar_sync: document.getElementById('calendar-sync').checked
                },
                processing: {
                    default_document_format: formData.get('default_document_format'),
                    max_file_size: parseInt(formData.get('max_file_size')),
                    auto_generate_documents: document.getElementById('auto-generate-docs').checked,
                    auto_start_batch: document.getElementById('auto-start-batch').checked
                },
                privacy: {
                    data_retention_days: parseInt(formData.get('data_retention_days')),
                    auto_delete_temp_files: document.getElementById('auto-delete-temp').checked,
                    share_analytics: document.getElementById('share-analytics').checked
                }
            };
            
            const response = await fetch(`${this.apiBaseUrl}/api/profile/preferences`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(preferencesData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Preferences updated successfully', 'success');
                
                // Update theme if changed
                const newTheme = preferencesData.theme;
                if (newTheme !== this.getCurrentTheme()) {
                    this.setTheme(newTheme);
                }
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Update preferences error:', error);
            this.showToast('Failed to update preferences', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async changePassword(e) {
        e.preventDefault();
        
        try {
            this.showLoading('Changing password...');
            
            const formData = new FormData(this.passwordForm);
            const passwordData = Object.fromEntries(formData.entries());
            
            const response = await fetch(`${this.apiBaseUrl}/api/profile/password`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(passwordData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Password changed successfully', 'success');
                this.passwordForm.reset();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Change password error:', error);
            this.showToast(error.message || 'Failed to change password', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async exportData() {
        try {
            this.showLoading('Exporting data...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/profile/export`, {
                credentials: 'include'
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Create and download JSON file
                const dataStr = JSON.stringify(result.data.export_data, null, 2);
                const dataBlob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(dataBlob);
                
                const a = document.createElement('a');
                a.href = url;
                a.download = `minutemate-data-export-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                this.showToast('Data exported successfully', 'success');
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Export data error:', error);
            this.showToast('Failed to export data', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async deleteAccount(e) {
        e.preventDefault();
        
        try {
            this.showLoading('Deleting account...');
            
            const formData = new FormData(this.deleteForm);
            const deleteData = Object.fromEntries(formData.entries());
            
            const response = await fetch(`${this.apiBaseUrl}/api/profile/delete`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(deleteData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Account deleted successfully', 'success');
                setTimeout(() => {
                    window.location.href = '/frontend/auth.html';
                }, 2000);
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Delete account error:', error);
            this.showToast(error.message || 'Failed to delete account', 'error');
        } finally {
            this.hideLoading();
            this.deleteModal.classList.remove('show');
        }
    }

    async logout() {
        try {
            await fetch(`${this.apiBaseUrl}/api/auth/logout`, {
                method: 'POST',
                credentials: 'include'
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/frontend/auth.html';
        }
    }

    // Theme management
    initializeTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
    }

    toggleTheme() {
        const currentTheme = this.getCurrentTheme();
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }

    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        const icon = this.themeToggle.querySelector('i');
        if (theme === 'dark') {
            icon.className = 'fas fa-sun';
            this.themeToggle.title = 'Switch to light mode';
        } else {
            icon.className = 'fas fa-moon';
            this.themeToggle.title = 'Switch to dark mode';
        }
    }

    // UI utilities
    showLoading(message = 'Loading...') {
        this.loadingOverlay.querySelector('p').textContent = message;
        this.loadingOverlay.classList.add('show');
    }

    hideLoading() {
        this.loadingOverlay.classList.remove('show');
    }

    showToast(message, type = 'info') {
        const toast = this.toast;
        const icon = toast.querySelector('.toast-icon i');
        const messageEl = toast.querySelector('.toast-message');
        
        messageEl.textContent = message;
        toast.className = `toast ${type}`;
        
        switch (type) {
            case 'success':
                icon.className = 'fas fa-check-circle';
                break;
            case 'error':
                icon.className = 'fas fa-exclamation-circle';
                break;
            case 'warning':
                icon.className = 'fas fa-exclamation-triangle';
                break;
            default:
                icon.className = 'fas fa-info-circle';
        }
        
        toast.classList.add('show');
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 5000);
    }
}

// Initialize the profile app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.profileApp = new ProfileApp();
});
