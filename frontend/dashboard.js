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
        this.userPreferences = document.getElementById('user-preferences');

        // Preferences modal elements
        this.preferencesModal = document.getElementById('preferences-modal');
        this.preferencesModalClose = document.getElementById('preferences-modal-close');
        this.preferencesCancel = document.getElementById('preferences-cancel');
        this.preferencesSave = document.getElementById('preferences-save');
        this.preferencesForm = document.getElementById('preferences-form');
        
        // Dashboard elements
        this.refreshBtn = document.getElementById('refresh-dashboard');
        this.recentMeetings = document.getElementById('recent-meetings');

        // Enhanced meeting history elements
        this.toggleFiltersBtn = document.getElementById('toggle-filters');
        this.meetingFilters = document.getElementById('meeting-filters');
        this.refreshMeetingsBtn = document.getElementById('refresh-meetings');
        this.searchInput = document.getElementById('search-input');
        this.statusFilter = document.getElementById('status-filter');
        this.dateFilter = document.getElementById('date-filter');
        this.sortBy = document.getElementById('sort-by');
        this.applyFiltersBtn = document.getElementById('apply-filters');
        this.clearFiltersBtn = document.getElementById('clear-filters');
        this.gridViewBtn = document.getElementById('grid-view');
        this.listViewBtn = document.getElementById('list-view');
        this.resultsCount = document.getElementById('results-count');
        this.resultsTotal = document.getElementById('results-total');
        this.paginationContainer = document.getElementById('pagination-container');
        this.paginationInfo = document.getElementById('pagination-info');
        this.prevPageBtn = document.getElementById('prev-page');
        this.nextPageBtn = document.getElementById('next-page');
        this.pageNumbers = document.getElementById('page-numbers');

        // Meeting history state
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.totalMeetings = 0;
        this.currentView = 'grid';
        this.currentFilters = {
            search: '',
            status: '',
            dateRange: '',
            sortBy: 'created_at_desc'
        };
        
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

        // Upload edited document elements
        this.uploadEditedModal = document.getElementById('upload-edited-modal');
        this.uploadEditedForm = document.getElementById('upload-edited-form');
        this.editedFileInput = document.getElementById('edited-file-input');
        this.comparisonResults = document.getElementById('comparison-results');
        
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

        // User preferences
        this.userPreferences.addEventListener('click', (e) => {
            e.preventDefault();
            this.showPreferencesModal();
        });

        // Preferences modal
        this.preferencesModalClose.addEventListener('click', () => {
            this.hidePreferencesModal();
        });

        this.preferencesCancel.addEventListener('click', () => {
            this.hidePreferencesModal();
        });

        this.preferencesSave.addEventListener('click', () => {
            this.saveUserPreferences();
        });

        // Close modal when clicking outside
        this.preferencesModal.addEventListener('click', (e) => {
            if (e.target === this.preferencesModal) {
                this.hidePreferencesModal();
            }
        });

        // Dashboard actions
        this.refreshBtn.addEventListener('click', this.loadDashboardData.bind(this));

        // Enhanced meeting history events
        this.toggleFiltersBtn.addEventListener('click', this.toggleFilters.bind(this));
        this.refreshMeetingsBtn.addEventListener('click', this.loadMeetings.bind(this));
        this.applyFiltersBtn.addEventListener('click', this.applyFilters.bind(this));
        this.clearFiltersBtn.addEventListener('click', this.clearFilters.bind(this));
        this.gridViewBtn.addEventListener('click', () => this.setView('grid'));
        this.listViewBtn.addEventListener('click', () => this.setView('list'));
        this.prevPageBtn.addEventListener('click', this.previousPage.bind(this));
        this.nextPageBtn.addEventListener('click', this.nextPage.bind(this));

        // Search input with debounce
        let searchTimeout;
        this.searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.currentFilters.search = this.searchInput.value;
                this.applyFilters();
            }, 500);
        });

        // Filter change events
        this.statusFilter.addEventListener('change', () => {
            this.currentFilters.status = this.statusFilter.value;
            this.applyFilters();
        });

        this.dateFilter.addEventListener('change', () => {
            this.currentFilters.dateRange = this.dateFilter.value;
            this.applyFilters();
        });

        this.sortBy.addEventListener('change', () => {
            this.currentFilters.sortBy = this.sortBy.value;
            this.applyFilters();
        });
        
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

        // Upload edited document
        this.uploadEditedForm.addEventListener('submit', this.uploadEditedDocument.bind(this));

        // Modal close handlers
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal) {
                    modal.classList.remove('show');
                }
            });
        });

        // Close modals when clicking outside
        this.uploadEditedModal.addEventListener('click', (e) => {
            if (e.target === this.uploadEditedModal) {
                this.uploadEditedModal.classList.remove('show');
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
                    // Load meetings with enhanced filtering
                    this.loadMeetings();
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
                        ${!meeting.has_edited_version ? `
                            <button class="btn-small secondary" onclick="dashboardApp.showUploadEditedModal('${meeting.id}')">
                                <i class="fas fa-upload"></i> Upload Edited
                            </button>
                        ` : `
                            <button class="btn-small success" onclick="dashboardApp.downloadPersonalized('${meeting.id}')">
                                <i class="fas fa-magic"></i> Personalized
                            </button>
                        `}
                    ` : ''}
                    <button class="btn-small secondary" onclick="dashboardApp.viewMeeting('${meeting.id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                </div>
                ${meeting.has_edited_version ? `
                    <div class="meeting-badges">
                        <span class="badge success">
                            <i class="fas fa-brain"></i> Preferences Learned
                        </span>
                    </div>
                ` : ''}
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

    // Upload edited document functionality
    showUploadEditedModal(meetingId) {
        this.currentMeetingId = meetingId;
        this.uploadEditedModal.classList.add('show');
        this.uploadEditedForm.reset();
        this.comparisonResults.innerHTML = '';
    }

    async uploadEditedDocument(e) {
        e.preventDefault();

        try {
            const fileInput = this.editedFileInput;
            if (!fileInput.files || fileInput.files.length === 0) {
                this.showToast('Please select a file to upload', 'error');
                return;
            }

            const file = fileInput.files[0];
            if (!file.name.toLowerCase().endsWith('.docx')) {
                this.showToast('Please upload a DOCX file', 'error');
                return;
            }

            this.showLoading('Uploading and analyzing document...');

            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${this.apiBaseUrl}/api/documents/upload-edited/${this.currentMeetingId}`, {
                method: 'POST',
                credentials: 'include',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.showToast('Document uploaded and preferences learned successfully!', 'success');
                this.displayComparisonSummary(result.data.comparison_summary);
                this.loadRecentMeetings(); // Refresh the meetings list

                // Auto-close modal after 3 seconds
                setTimeout(() => {
                    this.uploadEditedModal.classList.remove('show');
                }, 3000);
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Upload edited document error:', error);
            this.showToast(error.message || 'Failed to upload document', 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayComparisonSummary(summary) {
        this.comparisonResults.innerHTML = `
            <div class="comparison-summary">
                <h4><i class="fas fa-chart-line"></i> Analysis Results</h4>
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-value">${summary.preferences_learned}</span>
                        <span class="stat-label">Preferences Learned</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${Math.round(summary.confidence_score * 100)}%</span>
                        <span class="stat-label">Confidence Score</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${summary.content_changes}</span>
                        <span class="stat-label">Content Changes</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${summary.formatting_changes}</span>
                        <span class="stat-label">Format Changes</span>
                    </div>
                </div>
                <p class="summary-message">
                    <i class="fas fa-info-circle"></i>
                    Your preferences have been learned and will be applied to future documents automatically.
                </p>
            </div>
        `;
    }

    async downloadPersonalized(meetingId) {
        try {
            this.showLoading('Generating personalized document...');

            // First apply preferences
            const applyResponse = await fetch(`${this.apiBaseUrl}/api/documents/apply-preferences/${meetingId}`, {
                method: 'POST',
                credentials: 'include'
            });

            const applyResult = await applyResponse.json();

            if (applyResult.success && applyResult.data.personalized_document_available) {
                // Download the personalized document
                window.open(`${this.apiBaseUrl}/api/documents/download-personalized/${meetingId}`, '_blank');
                this.showToast('Personalized document downloaded successfully', 'success');
            } else {
                // Fall back to regular download
                window.open(`${this.apiBaseUrl}/api/meetings/${meetingId}/download`, '_blank');
                this.showToast('Downloaded original document (no personalization available)', 'info');
            }
        } catch (error) {
            console.error('Download personalized error:', error);
            this.showToast('Failed to download personalized document', 'error');
        } finally {
            this.hideLoading();
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

    async showPreferencesModal() {
        try {
            // Load current user preferences
            await this.loadUserPreferences();
            this.preferencesModal.style.display = 'flex';
            this.userDropdown.classList.remove('show');
        } catch (error) {
            console.error('Error loading preferences:', error);
            this.showToast('Failed to load preferences', 'error');
        }
    }

    hidePreferencesModal() {
        this.preferencesModal.style.display = 'none';
    }

    async loadUserPreferences() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/auth/preferences`, {
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.populatePreferencesForm(result.data.preferences);
                } else {
                    // Use default preferences if none exist
                    this.populatePreferencesForm({});
                }
            } else {
                throw new Error('Failed to load preferences');
            }
        } catch (error) {
            console.error('Error loading user preferences:', error);
            // Use default preferences
            this.populatePreferencesForm({});
        }
    }

    populatePreferencesForm(preferences) {
        // Set form values from preferences or defaults
        document.getElementById('default-template').value = preferences.default_template || 'professional';
        document.getElementById('default-language').value = preferences.default_language || 'auto';
        document.getElementById('user-timezone').value = preferences.timezone || this.currentUser?.timezone || 'UTC';
        document.getElementById('user-theme').value = preferences.theme || this.currentUser?.theme || 'light';
        document.getElementById('email-notifications').checked = preferences.email_notifications !== false;
        document.getElementById('processing-notifications').checked = preferences.processing_notifications !== false;
    }

    async saveUserPreferences() {
        try {
            const formData = new FormData(this.preferencesForm);
            const preferences = {};

            // Convert form data to object
            for (let [key, value] of formData.entries()) {
                if (key.includes('notifications')) {
                    preferences[key] = true; // Checkbox is checked if present
                } else {
                    preferences[key] = value;
                }
            }

            // Set unchecked checkboxes to false
            preferences.email_notifications = document.getElementById('email-notifications').checked;
            preferences.processing_notifications = document.getElementById('processing-notifications').checked;

            const response = await fetch(`${this.apiBaseUrl}/api/auth/preferences`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(preferences)
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.showToast('Preferences saved successfully', 'success');
                    this.hidePreferencesModal();

                    // Update current user data if theme changed
                    if (preferences.theme !== this.currentUser?.theme) {
                        this.currentUser.theme = preferences.theme;
                        this.applyTheme(preferences.theme);
                    }
                } else {
                    throw new Error(result.message);
                }
            } else {
                throw new Error('Failed to save preferences');
            }
        } catch (error) {
            console.error('Error saving preferences:', error);
            this.showToast('Failed to save preferences', 'error');
        }
    }

    applyTheme(theme) {
        if (theme === 'auto') {
            // Use system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.body.classList.toggle('dark-theme', prefersDark);
        } else {
            document.body.classList.toggle('dark-theme', theme === 'dark');
        }
    }

    // Enhanced Meeting History Methods
    toggleFilters() {
        const isVisible = this.meetingFilters.style.display !== 'none';
        this.meetingFilters.style.display = isVisible ? 'none' : 'block';
        this.toggleFiltersBtn.innerHTML = isVisible ?
            '<i class="fas fa-filter"></i> Filters' :
            '<i class="fas fa-filter"></i> Hide Filters';
    }

    async loadMeetings() {
        try {
            this.showLoading('Loading meetings...');

            // Build query parameters
            const params = new URLSearchParams({
                page: this.currentPage,
                limit: this.itemsPerPage,
                search: this.currentFilters.search,
                status: this.currentFilters.status,
                date_range: this.currentFilters.dateRange,
                sort_by: this.currentFilters.sortBy
            });

            const response = await fetch(`${this.apiBaseUrl}/api/meetings/list?${params}`, {
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.updateMeetingsList(result.data.meetings);
                    this.updatePagination(result.data.pagination);
                    this.updateResultsInfo(result.data.pagination);
                } else {
                    throw new Error(result.message);
                }
            } else {
                throw new Error('Failed to load meetings');
            }
        } catch (error) {
            console.error('Error loading meetings:', error);
            this.showToast('Failed to load meetings', 'error');
            this.recentMeetings.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error loading meetings</h3>
                    <p>Please try refreshing the page.</p>
                </div>
            `;
        } finally {
            this.hideLoading();
        }
    }

    updateMeetingsList(meetings) {
        if (!meetings || meetings.length === 0) {
            this.recentMeetings.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>No meetings found</h3>
                    <p>Try adjusting your filters or search terms.</p>
                    <button class="btn primary" id="clear-search-filters">Clear Filters</button>
                </div>
            `;

            // Add event listener for clear filters button
            const clearBtn = document.getElementById('clear-search-filters');
            if (clearBtn) {
                clearBtn.addEventListener('click', this.clearFilters.bind(this));
            }
            return;
        }

        const meetingsHtml = meetings.map(meeting => `
            <div class="meeting-card" data-meeting-id="${meeting.id}">
                <div class="meeting-header">
                    <h4 class="meeting-title">${meeting.title || 'Untitled Meeting'}</h4>
                    <span class="meeting-status status-${meeting.status}">${meeting.status}</span>
                </div>
                <div class="meeting-info">
                    <div class="meeting-meta">
                        <span><i class="fas fa-calendar"></i> ${new Date(meeting.created_at).toLocaleDateString()}</span>
                        <span><i class="fas fa-clock"></i> ${meeting.duration || 'N/A'}</span>
                        ${meeting.attendees_count ? `<span><i class="fas fa-users"></i> ${meeting.attendees_count} attendees</span>` : ''}
                    </div>
                    <div class="meeting-actions">
                        <button class="btn secondary small" onclick="dashboardApp.viewMeeting('${meeting.id}')">
                            <i class="fas fa-eye"></i> View
                        </button>
                        ${meeting.status === 'completed' ? `
                            <button class="btn primary small" onclick="dashboardApp.downloadMeeting('${meeting.id}')">
                                <i class="fas fa-download"></i> Download
                            </button>
                        ` : ''}
                        <button class="btn secondary small" onclick="dashboardApp.deleteMeeting('${meeting.id}')">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        this.recentMeetings.innerHTML = meetingsHtml;
        this.recentMeetings.className = `recent-meetings ${this.currentView}-view`;
    }

    updatePagination(pagination) {
        this.totalMeetings = pagination.total;
        const totalPages = Math.ceil(pagination.total / this.itemsPerPage);

        if (totalPages <= 1) {
            this.paginationContainer.style.display = 'none';
            return;
        }

        this.paginationContainer.style.display = 'flex';

        // Update pagination info
        const start = (this.currentPage - 1) * this.itemsPerPage + 1;
        const end = Math.min(this.currentPage * this.itemsPerPage, pagination.total);
        this.paginationInfo.textContent = `Showing ${start}-${end} of ${pagination.total} meetings`;

        // Update navigation buttons
        this.prevPageBtn.disabled = this.currentPage <= 1;
        this.nextPageBtn.disabled = this.currentPage >= totalPages;

        // Generate page numbers
        this.generatePageNumbers(totalPages);
    }

    generatePageNumbers(totalPages) {
        const maxVisible = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(totalPages, startPage + maxVisible - 1);

        if (endPage - startPage + 1 < maxVisible) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }

        let pagesHtml = '';

        // First page and ellipsis
        if (startPage > 1) {
            pagesHtml += `<button class="page-number" onclick="dashboardApp.goToPage(1)">1</button>`;
            if (startPage > 2) {
                pagesHtml += `<span class="page-ellipsis">...</span>`;
            }
        }

        // Page numbers
        for (let i = startPage; i <= endPage; i++) {
            pagesHtml += `<button class="page-number ${i === this.currentPage ? 'active' : ''}"
                         onclick="dashboardApp.goToPage(${i})">${i}</button>`;
        }

        // Last page and ellipsis
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                pagesHtml += `<span class="page-ellipsis">...</span>`;
            }
            pagesHtml += `<button class="page-number" onclick="dashboardApp.goToPage(${totalPages})">${totalPages}</button>`;
        }

        this.pageNumbers.innerHTML = pagesHtml;
    }

    updateResultsInfo(pagination) {
        this.resultsCount.textContent = `${pagination.total} meetings`;
        this.resultsTotal.textContent = pagination.total > 0 ?
            `(${pagination.filtered} filtered)` : '';
    }

    applyFilters() {
        this.currentPage = 1; // Reset to first page
        this.loadMeetings();
    }

    clearFilters() {
        this.currentFilters = {
            search: '',
            status: '',
            dateRange: '',
            sortBy: 'created_at_desc'
        };

        // Reset form elements
        this.searchInput.value = '';
        this.statusFilter.value = '';
        this.dateFilter.value = '';
        this.sortBy.value = 'created_at_desc';

        this.applyFilters();
    }

    setView(view) {
        this.currentView = view;
        this.gridViewBtn.classList.toggle('active', view === 'grid');
        this.listViewBtn.classList.toggle('active', view === 'list');
        this.recentMeetings.className = `recent-meetings ${view}-view`;
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadMeetings();
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadMeetings();
        }
    }

    nextPage() {
        const totalPages = Math.ceil(this.totalMeetings / this.itemsPerPage);
        if (this.currentPage < totalPages) {
            this.currentPage++;
            this.loadMeetings();
        }
    }

    async downloadMeeting(meetingId) {
        try {
            this.showLoading('Preparing download...');

            const response = await fetch(`${this.apiBaseUrl}/api/meetings/${meetingId}/download`, {
                credentials: 'include'
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `meeting-${meetingId}.docx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                this.showToast('Meeting downloaded successfully', 'success');
            } else {
                throw new Error('Failed to download meeting');
            }
        } catch (error) {
            console.error('Error downloading meeting:', error);
            this.showToast('Failed to download meeting', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async deleteMeeting(meetingId) {
        if (!confirm('Are you sure you want to delete this meeting? This action cannot be undone.')) {
            return;
        }

        try {
            this.showLoading('Deleting meeting...');

            const response = await fetch(`${this.apiBaseUrl}/api/meetings/${meetingId}`, {
                method: 'DELETE',
                credentials: 'include'
            });

            if (response.ok) {
                this.showToast('Meeting deleted successfully', 'success');
                this.loadMeetings(); // Refresh the list
            } else {
                throw new Error('Failed to delete meeting');
            }
        } catch (error) {
            console.error('Error deleting meeting:', error);
            this.showToast('Failed to delete meeting', 'error');
        } finally {
            this.hideLoading();
        }
    }
}

// Initialize the dashboard app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardApp = new DashboardApp();
});
