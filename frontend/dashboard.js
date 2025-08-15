/**
 * MinuteMate Dashboard JavaScript
 * Handles dashboard functionality, meeting history, and user management
 */

class DashboardApp {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.currentUser = null;
        
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
        
        // Dashboard elements
        this.refreshBtn = document.getElementById('refresh-dashboard');
        this.recentMeetings = document.getElementById('recent-meetings');
        
        // Statistics elements
        this.totalMeetings = document.getElementById('total-meetings');
        this.completedMeetings = document.getElementById('completed-meetings');
        this.pendingMeetings = document.getElementById('pending-meetings');
        this.successRate = document.getElementById('success-rate');
        
        // Search elements
        this.searchModal = document.getElementById('search-modal');
        this.searchInput = document.getElementById('search-input');
        this.searchBtn = document.getElementById('search-btn');
        this.searchResults = document.getElementById('search-results');
        
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

        // Dashboard actions
        this.refreshBtn.addEventListener('click', this.loadDashboardData.bind(this));
        
        // Search functionality
        document.getElementById('search-meetings').addEventListener('click', this.openSearchModal.bind(this));
        this.searchModal.querySelector('.search-modal-close').addEventListener('click', this.closeSearchModal.bind(this));
        this.searchBtn.addEventListener('click', this.performSearch.bind(this));
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        // Quick actions
        document.getElementById('view-templates').addEventListener('click', () => {
            window.location.href = '/frontend/templates.html';
        });
        
        document.getElementById('export-data').addEventListener('click', () => {
            this.showToast('Export feature coming soon!', 'info');
        });

        // View all meetings
        document.getElementById('view-all-meetings').addEventListener('click', (e) => {
            e.preventDefault();
            this.showToast('Full meeting history page coming soon!', 'info');
        });

        // Logout
        document.getElementById('user-logout').addEventListener('click', this.logout.bind(this));
        
        // Theme toggle
        this.themeToggle.addEventListener('click', this.toggleTheme.bind(this));
        
        // Toast close
        this.toast.querySelector('.toast-close').addEventListener('click', () => {
            this.toast.classList.remove('show');
        });

        // Close search modal when clicking outside
        this.searchModal.addEventListener('click', (e) => {
            if (e.target === this.searchModal) {
                this.closeSearchModal();
            }
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
            this.loadDashboardData();
            
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

    async loadDashboardData() {
        try {
            this.showLoading('Loading dashboard...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/meetings/dashboard`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.updateStatistics(result.data.statistics);
                    this.updateRecentMeetings(result.data.recent_meetings);
                } else {
                    throw new Error(result.message);
                }
            } else {
                throw new Error('Failed to load dashboard data');
            }
        } catch (error) {
            console.error('Dashboard load error:', error);
            this.showToast('Failed to load dashboard data', 'error');
        } finally {
            this.hideLoading();
        }
    }

    updateStatistics(stats) {
        this.totalMeetings.textContent = stats.total_meetings || 0;
        this.completedMeetings.textContent = stats.completed_meetings || 0;
        this.pendingMeetings.textContent = stats.pending_meetings || 0;
        this.successRate.textContent = `${stats.success_rate || 0}%`;
    }

    updateRecentMeetings(meetings) {
        if (!meetings || meetings.length === 0) {
            this.recentMeetings.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-calendar-plus"></i>
                    <h3>No meetings yet</h3>
                    <p>Upload your first meeting recording to get started!</p>
                    <button class="btn primary" onclick="window.location.href='/frontend/'">
                        <i class="fas fa-plus"></i> Create First Meeting
                    </button>
                </div>
            `;
            return;
        }

        const meetingsHtml = meetings.map(meeting => `
            <div class="meeting-card" data-meeting-id="${meeting.id}">
                <div class="meeting-header">
                    <h4>${meeting.title}</h4>
                    <span class="meeting-status status-${meeting.status}">${meeting.status}</span>
                </div>
                <div class="meeting-meta">
                    <span class="meeting-date">
                        <i class="fas fa-calendar"></i>
                        ${new Date(meeting.created_at).toLocaleDateString()}
                    </span>
                    ${meeting.duration_minutes ? `
                        <span class="meeting-duration">
                            <i class="fas fa-clock"></i>
                            ${meeting.duration_minutes} min
                        </span>
                    ` : ''}
                </div>
                ${meeting.description ? `<p class="meeting-description">${meeting.description}</p>` : ''}
                <div class="meeting-actions">
                    ${meeting.status === 'completed' ? `
                        <button class="btn-small primary" onclick="window.open('/api/download/${meeting.job_id}', '_blank')">
                            <i class="fas fa-download"></i> Download
                        </button>
                    ` : ''}
                    <button class="btn-small secondary" onclick="dashboardApp.viewMeeting('${meeting.id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                </div>
            </div>
        `).join('');

        this.recentMeetings.innerHTML = meetingsHtml;
    }

    async viewMeeting(meetingId) {
        try {
            this.showLoading('Loading meeting...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/meetings/${meetingId}`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.showMeetingDetails(result.data.meeting);
                } else {
                    throw new Error(result.message);
                }
            } else {
                throw new Error('Failed to load meeting');
            }
        } catch (error) {
            console.error('Meeting load error:', error);
            this.showToast('Failed to load meeting details', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showMeetingDetails(meeting) {
        // For now, show a simple alert with meeting info
        // In a full implementation, this would open a detailed modal
        const info = `
Meeting: ${meeting.title}
Status: ${meeting.status}
Created: ${new Date(meeting.created_at).toLocaleString()}
${meeting.description ? `Description: ${meeting.description}` : ''}
${meeting.attendees ? `Attendees: ${meeting.attendees.length}` : ''}
        `;
        alert(info);
    }

    openSearchModal() {
        this.searchModal.classList.add('show');
        this.searchInput.focus();
    }

    closeSearchModal() {
        this.searchModal.classList.remove('show');
        this.searchInput.value = '';
        this.searchResults.innerHTML = `
            <div class="search-placeholder">
                <i class="fas fa-search"></i>
                <p>Enter a search term to find your meetings</p>
            </div>
        `;
    }

    async performSearch() {
        const query = this.searchInput.value.trim();
        if (!query) {
            this.showToast('Please enter a search term', 'warning');
            return;
        }

        try {
            this.searchResults.innerHTML = `
                <div class="search-loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Searching...</p>
                </div>
            `;

            const response = await fetch(`${this.apiBaseUrl}/api/meetings/search?q=${encodeURIComponent(query)}`, {
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.displaySearchResults(result.data.meetings);
                } else {
                    throw new Error(result.message);
                }
            } else {
                throw new Error('Search failed');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.searchResults.innerHTML = `
                <div class="search-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Search failed. Please try again.</p>
                </div>
            `;
        }
    }

    displaySearchResults(meetings) {
        if (!meetings || meetings.length === 0) {
            this.searchResults.innerHTML = `
                <div class="search-empty">
                    <i class="fas fa-search"></i>
                    <p>No meetings found matching your search.</p>
                </div>
            `;
            return;
        }

        const resultsHtml = meetings.map(meeting => `
            <div class="search-result" onclick="dashboardApp.viewMeeting('${meeting.id}')">
                <h4>${meeting.title}</h4>
                <p class="search-meta">
                    <span class="status-${meeting.status}">${meeting.status}</span>
                    • ${new Date(meeting.created_at).toLocaleDateString()}
                </p>
                ${meeting.description ? `<p class="search-description">${meeting.description}</p>` : ''}
            </div>
        `).join('');

        this.searchResults.innerHTML = resultsHtml;
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
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
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

// Initialize the dashboard app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardApp = new DashboardApp();
});
