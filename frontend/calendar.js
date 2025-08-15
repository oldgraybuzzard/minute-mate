/**
 * MinuteMate Calendar JavaScript
 * Handles calendar integration, event management, and synchronization
 */

class CalendarApp {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.currentUser = null;
        this.integrations = [];
        this.providers = [];
        this.currentMeetingId = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.initializeTheme();
        this.checkAuthentication();
        this.handleUrlParams();
    }

    initializeElements() {
        // User elements
        this.userMenuToggle = document.getElementById('user-menu-toggle');
        this.userDropdown = document.getElementById('user-dropdown');
        this.userName = document.getElementById('user-name');
        this.userFullName = document.getElementById('user-full-name');
        this.userEmail = document.getElementById('user-email');
        
        // Calendar elements
        this.integrationsGrid = document.getElementById('integrations-grid');
        this.upcomingEvents = document.getElementById('upcoming-events');
        this.unprocessedEvents = document.getElementById('unprocessed-events');
        this.connectCalendarBtn = document.getElementById('connect-calendar-btn');
        this.syncAllBtn = document.getElementById('sync-all-btn');
        this.statusMessage = document.getElementById('status-message');
        this.statusText = document.getElementById('status-text');
        
        // Modal elements
        this.connectModal = document.getElementById('connect-modal');
        this.providersGrid = document.getElementById('providers-grid');
        this.followupModal = document.getElementById('followup-modal');
        this.followupForm = document.getElementById('followup-form');
        this.confirmationModal = document.getElementById('confirmation-modal');
        this.confirmationMessage = document.getElementById('confirmation-message');
        this.confirmActionBtn = document.getElementById('confirm-action');
        
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

        // Calendar actions
        this.connectCalendarBtn.addEventListener('click', () => this.openConnectModal());
        this.syncAllBtn.addEventListener('click', () => this.syncAllCalendars());
        
        // Modal actions
        this.connectModal.querySelector('.connect-modal-close').addEventListener('click', () => this.closeConnectModal());
        this.followupModal.querySelector('.followup-modal-close').addEventListener('click', () => this.closeFollowupModal());
        this.followupForm.addEventListener('submit', this.createFollowupEvent.bind(this));
        document.getElementById('cancel-followup').addEventListener('click', () => this.closeFollowupModal());
        
        // Confirmation modal
        document.getElementById('cancel-confirmation').addEventListener('click', () => this.closeConfirmationModal());
        
        // Close modals when clicking outside
        [this.connectModal, this.followupModal, this.confirmationModal].forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('show');
                }
            });
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

    handleUrlParams() {
        const urlParams = new URLSearchParams(window.location.search);
        const success = urlParams.get('success');
        const error = urlParams.get('error');
        
        if (success === 'connected') {
            this.showStatusMessage('Calendar connected successfully!', 'success');
            this.loadIntegrations();
        } else if (error) {
            this.showStatusMessage(`Connection failed: ${error}`, 'error');
        }
        
        // Clean up URL
        if (success || error) {
            window.history.replaceState({}, document.title, window.location.pathname);
        }
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
            this.loadProviders();
            this.loadIntegrations();
            this.loadUpcomingEvents();
            this.loadUnprocessedEvents();
            
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

    async loadProviders() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/calendar/providers`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.providers = result.data.providers;
                }
            }
        } catch (error) {
            console.error('Failed to load providers:', error);
        }
    }

    async loadIntegrations() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/calendar/integrations`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.integrations = result.data.integrations;
                    this.renderIntegrations();
                } else {
                    throw new Error(result.message);
                }
            } else {
                throw new Error('Failed to load integrations');
            }
        } catch (error) {
            console.error('Integrations load error:', error);
            this.integrationsGrid.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Failed to load integrations</h3>
                    <p>Please try refreshing the page</p>
                </div>
            `;
        }
    }

    renderIntegrations() {
        if (!this.integrations || this.integrations.length === 0) {
            this.integrationsGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-calendar-alt"></i>
                    <h3>No calendars connected</h3>
                    <p>Connect your first calendar to start syncing events!</p>
                    <button class="btn primary" onclick="calendarApp.openConnectModal()">
                        <i class="fas fa-plus"></i> Connect Calendar
                    </button>
                </div>
            `;
            return;
        }

        const integrationsHtml = this.integrations.map(integration => `
            <div class="integration-card" data-integration-id="${integration.id}">
                <div class="integration-header">
                    <div class="integration-info">
                        <div class="integration-provider">
                            <i class="${this.getProviderIcon(integration.provider)}"></i>
                            <span>${this.getProviderName(integration.provider)}</span>
                        </div>
                        <div class="integration-email">${integration.provider_email}</div>
                    </div>
                    <div class="integration-status">
                        <span class="status-badge status-${integration.sync_status}">${integration.sync_status}</span>
                    </div>
                </div>
                
                <div class="integration-body">
                    <div class="integration-meta">
                        <div class="meta-item">
                            <strong>Last Sync:</strong>
                            <span>${integration.last_sync_at ? new Date(integration.last_sync_at).toLocaleString() : 'Never'}</span>
                        </div>
                        <div class="meta-item">
                            <strong>Auto Import:</strong>
                            <span>${integration.auto_import_events ? 'Enabled' : 'Disabled'}</span>
                        </div>
                    </div>
                    
                    ${integration.sync_error_message ? `
                        <div class="error-message">
                            <i class="fas fa-exclamation-triangle"></i>
                            ${integration.sync_error_message}
                        </div>
                    ` : ''}
                </div>
                
                <div class="integration-actions">
                    <button class="btn-small secondary" onclick="calendarApp.syncIntegration('${integration.id}')">
                        <i class="fas fa-sync-alt"></i> Sync
                    </button>
                    <button class="btn-small danger" onclick="calendarApp.disconnectIntegration('${integration.id}')">
                        <i class="fas fa-unlink"></i> Disconnect
                    </button>
                </div>
            </div>
        `).join('');

        this.integrationsGrid.innerHTML = integrationsHtml;
    }

    getProviderIcon(provider) {
        const icons = {
            'google': 'fab fa-google',
            'outlook': 'fab fa-microsoft'
        };
        return icons[provider] || 'fas fa-calendar';
    }

    getProviderName(provider) {
        const names = {
            'google': 'Google Calendar',
            'outlook': 'Microsoft Outlook'
        };
        return names[provider] || provider;
    }

    async loadUpcomingEvents() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/calendar/events/upcoming?days=7`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.renderUpcomingEvents(result.data.events);
                }
            }
        } catch (error) {
            console.error('Failed to load upcoming events:', error);
        }
    }

    renderUpcomingEvents(events) {
        if (!events || events.length === 0) {
            this.upcomingEvents.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-calendar"></i>
                    <h3>No upcoming events</h3>
                    <p>Your upcoming calendar events will appear here</p>
                </div>
            `;
            return;
        }

        const eventsHtml = events.map(event => `
            <div class="event-card">
                <div class="event-time">
                    <div class="event-date">${new Date(event.start_time).toLocaleDateString()}</div>
                    <div class="event-time-range">
                        ${new Date(event.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - 
                        ${new Date(event.end_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </div>
                </div>
                <div class="event-details">
                    <h4>${event.title}</h4>
                    ${event.location ? `<p class="event-location"><i class="fas fa-map-marker-alt"></i> ${event.location}</p>` : ''}
                    ${event.description ? `<p class="event-description">${event.description.substring(0, 100)}${event.description.length > 100 ? '...' : ''}</p>` : ''}
                </div>
                <div class="event-actions">
                    <button class="btn-small primary" onclick="calendarApp.createFollowupFromEvent('${event.id}')">
                        <i class="fas fa-calendar-plus"></i> Follow-up
                    </button>
                </div>
            </div>
        `).join('');

        this.upcomingEvents.innerHTML = eventsHtml;
    }

    async loadUnprocessedEvents() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/calendar/events/unprocessed`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.renderUnprocessedEvents(result.data.events);
                }
            }
        } catch (error) {
            console.error('Failed to load unprocessed events:', error);
        }
    }

    renderUnprocessedEvents(events) {
        if (!events || events.length === 0) {
            this.unprocessedEvents.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle"></i>
                    <h3>All caught up!</h3>
                    <p>No events need meeting minutes</p>
                </div>
            `;
            return;
        }

        const eventsHtml = events.map(event => `
            <div class="event-card unprocessed">
                <div class="event-time">
                    <div class="event-date">${new Date(event.start_time).toLocaleDateString()}</div>
                    <div class="event-time-range">
                        ${new Date(event.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - 
                        ${new Date(event.end_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </div>
                </div>
                <div class="event-details">
                    <h4>${event.title}</h4>
                    ${event.location ? `<p class="event-location"><i class="fas fa-map-marker-alt"></i> ${event.location}</p>` : ''}
                    <p class="event-status"><i class="fas fa-exclamation-triangle"></i> Needs meeting minutes</p>
                </div>
                <div class="event-actions">
                    <button class="btn-small primary" onclick="window.location.href='/frontend/?event_id=${event.id}'">
                        <i class="fas fa-upload"></i> Upload Recording
                    </button>
                    <button class="btn-small secondary" onclick="calendarApp.markEventProcessed('${event.id}')">
                        <i class="fas fa-check"></i> Mark Done
                    </button>
                </div>
            </div>
        `).join('');

        this.unprocessedEvents.innerHTML = eventsHtml;
    }

    openConnectModal() {
        this.renderProviders();
        this.connectModal.classList.add('show');
    }

    closeConnectModal() {
        this.connectModal.classList.remove('show');
    }

    renderProviders() {
        const providersHtml = this.providers.map(provider => `
            <div class="provider-card" onclick="calendarApp.connectProvider('${provider.id}')">
                <div class="provider-icon" style="color: ${provider.color}">
                    <i class="${provider.icon}"></i>
                </div>
                <div class="provider-info">
                    <h4>${provider.name}</h4>
                    <p>${provider.description}</p>
                </div>
            </div>
        `).join('');

        this.providersGrid.innerHTML = providersHtml;
    }

    async connectProvider(provider) {
        try {
            this.showLoading('Connecting to calendar...');
            
            const redirectUri = `${window.location.origin}/api/calendar/callback?provider=${provider}`;
            const response = await fetch(`${this.apiBaseUrl}/api/calendar/connect/${provider}?redirect_uri=${encodeURIComponent(redirectUri)}`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // Redirect to OAuth URL
                    window.location.href = result.data.auth_url;
                } else {
                    throw new Error(result.message);
                }
            } else {
                throw new Error('Failed to initiate connection');
            }
        } catch (error) {
            console.error('Connect provider error:', error);
            this.showToast('Failed to connect calendar', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async syncIntegration(integrationId) {
        try {
            this.showLoading('Syncing calendar...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/calendar/integrations/${integrationId}/sync`, {
                method: 'POST',
                credentials: 'include'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast(`Sync completed: ${result.data.imported_count} new, ${result.data.updated_count} updated`, 'success');
                this.loadIntegrations();
                this.loadUpcomingEvents();
                this.loadUnprocessedEvents();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Sync integration error:', error);
            this.showToast('Failed to sync calendar', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async syncAllCalendars() {
        try {
            this.showLoading('Syncing all calendars...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/calendar/sync-all`, {
                method: 'POST',
                credentials: 'include'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast(result.message, 'success');
                this.loadIntegrations();
                this.loadUpcomingEvents();
                this.loadUnprocessedEvents();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Sync all calendars error:', error);
            this.showToast('Failed to sync calendars', 'error');
        } finally {
            this.hideLoading();
        }
    }

    disconnectIntegration(integrationId) {
        this.confirmationMessage.textContent = 'Are you sure you want to disconnect this calendar? All imported events will be removed.';
        this.confirmActionBtn.onclick = () => this.confirmDisconnectIntegration(integrationId);
        this.confirmationModal.classList.add('show');
    }

    async confirmDisconnectIntegration(integrationId) {
        try {
            this.closeConfirmationModal();
            this.showLoading('Disconnecting calendar...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/calendar/integrations/${integrationId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Calendar disconnected successfully', 'success');
                this.loadIntegrations();
                this.loadUpcomingEvents();
                this.loadUnprocessedEvents();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Disconnect integration error:', error);
            this.showToast('Failed to disconnect calendar', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async markEventProcessed(eventId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/calendar/events/${eventId}/process`, {
                method: 'POST',
                credentials: 'include'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Event marked as processed', 'success');
                this.loadUnprocessedEvents();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Mark event processed error:', error);
            this.showToast('Failed to mark event as processed', 'error');
        }
    }

    createFollowupFromEvent(eventId) {
        // Pre-fill form with event data
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(10, 0, 0, 0);
        
        const endTime = new Date(tomorrow);
        endTime.setHours(11, 0, 0, 0);
        
        document.getElementById('followup-title').value = 'Follow-up Meeting';
        document.getElementById('followup-start').value = tomorrow.toISOString().slice(0, 16);
        document.getElementById('followup-end').value = endTime.toISOString().slice(0, 16);
        document.getElementById('followup-meeting-id').value = eventId;
        
        this.followupModal.classList.add('show');
    }

    closeFollowupModal() {
        this.followupModal.classList.remove('show');
        this.followupForm.reset();
    }

    async createFollowupEvent(e) {
        e.preventDefault();
        
        try {
            this.showLoading('Creating follow-up event...');
            
            const formData = new FormData(this.followupForm);
            const eventData = {
                meeting_id: formData.get('meeting_id'),
                title: formData.get('title'),
                description: formData.get('description'),
                start_time: new Date(formData.get('start_time')).toISOString(),
                end_time: new Date(formData.get('end_time')).toISOString(),
                location: formData.get('location'),
                attendees: formData.get('attendees') ? formData.get('attendees').split(',').map(email => email.trim()) : []
            };
            
            const response = await fetch(`${this.apiBaseUrl}/api/calendar/events/follow-up`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(eventData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Follow-up event created successfully', 'success');
                this.closeFollowupModal();
                this.loadUpcomingEvents();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Create follow-up event error:', error);
            this.showToast('Failed to create follow-up event', 'error');
        } finally {
            this.hideLoading();
        }
    }

    closeConfirmationModal() {
        this.confirmationModal.classList.remove('show');
    }

    showStatusMessage(message, type) {
        this.statusText.textContent = message;
        this.statusMessage.className = `status-message ${type}`;
        this.statusMessage.style.display = 'block';
        
        setTimeout(() => {
            this.statusMessage.style.display = 'none';
        }, 5000);
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

// Initialize the calendar app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.calendarApp = new CalendarApp();
});
