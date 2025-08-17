/**
 * Real-time Manager
 * Handles WebSocket connections, live updates, and real-time notifications
 */

class RealtimeManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = null;
        this.listeners = new Map();
        this.isConnected = false;
        
        this.initializeConnection();
        this.setupEventListeners();
    }

    initializeConnection() {
        // For now, we'll simulate WebSocket with polling
        // In a real implementation, you'd use actual WebSocket
        this.startPolling();
    }

    setupEventListeners() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });

        // Handle online/offline status
        window.addEventListener('online', () => {
            this.handleOnline();
        });

        window.addEventListener('offline', () => {
            this.handleOffline();
        });
    }

    // Simulated WebSocket with polling for real-time updates
    startPolling() {
        this.pollingInterval = setInterval(() => {
            this.checkForUpdates();
        }, 30000); // Check every 30 seconds
    }

    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    async checkForUpdates() {
        try {
            const response = await fetch('/api/realtime/updates', {
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data.updates) {
                    this.processUpdates(result.data.updates);
                }
            }
        } catch (error) {
            console.error('Error checking for updates:', error);
        }
    }

    processUpdates(updates) {
        updates.forEach(update => {
            this.emit(update.type, update.data);
        });
    }

    // Event system for real-time updates
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Error in event callback:', error);
                }
            });
        }
    }

    // Meeting status updates
    subscribeToMeetingUpdates(meetingId, callback) {
        this.on(`meeting:${meetingId}:status`, callback);
        this.on(`meeting:${meetingId}:progress`, callback);
    }

    unsubscribeFromMeetingUpdates(meetingId, callback) {
        this.off(`meeting:${meetingId}:status`, callback);
        this.off(`meeting:${meetingId}:progress`, callback);
    }

    // Global meeting updates
    subscribeToGlobalUpdates(callback) {
        this.on('meeting:created', callback);
        this.on('meeting:completed', callback);
        this.on('meeting:deleted', callback);
        this.on('meeting:shared', callback);
    }

    // Connection management
    pauseUpdates() {
        this.stopPolling();
    }

    resumeUpdates() {
        if (!this.pollingInterval) {
            this.startPolling();
        }
    }

    handleOnline() {
        this.isConnected = true;
        this.resumeUpdates();
        window.loadingManager?.showToast('Connection restored', 'success', 3000);
    }

    handleOffline() {
        this.isConnected = false;
        this.pauseUpdates();
        window.loadingManager?.showToast('Connection lost - working offline', 'warning', 5000);
    }

    // Simulate real-time meeting progress updates
    simulateMeetingProgress(meetingId, callback) {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                callback({ meetingId, progress, status: 'completed' });
            } else {
                callback({ meetingId, progress, status: 'processing' });
            }
        }, 1000);
        return interval;
    }

    // Live notifications
    showLiveNotification(title, message, type = 'info') {
        // Check if notifications are supported and permitted
        if ('Notification' in window && Notification.permission === 'granted') {
            const notification = new Notification(title, {
                body: message,
                icon: '/frontend/images/logo.png',
                badge: '/frontend/images/logo.png',
                tag: 'minutemate-notification'
            });

            notification.onclick = () => {
                window.focus();
                notification.close();
            };

            // Auto close after 5 seconds
            setTimeout(() => {
                notification.close();
            }, 5000);
        } else {
            // Fallback to toast notification
            window.loadingManager?.showToast(`${title}: ${message}`, type);
        }
    }

    // Request notification permission
    async requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            return permission === 'granted';
        }
        return Notification.permission === 'granted';
    }

    // Background sync for offline actions
    queueOfflineAction(action, data) {
        const offlineQueue = JSON.parse(localStorage.getItem('offlineQueue') || '[]');
        offlineQueue.push({
            id: Date.now(),
            action,
            data,
            timestamp: new Date().toISOString()
        });
        localStorage.setItem('offlineQueue', JSON.stringify(offlineQueue));
    }

    async processOfflineQueue() {
        const offlineQueue = JSON.parse(localStorage.getItem('offlineQueue') || '[]');
        if (offlineQueue.length === 0) return;

        const processedIds = [];
        
        for (const item of offlineQueue) {
            try {
                await this.executeOfflineAction(item);
                processedIds.push(item.id);
            } catch (error) {
                console.error('Error processing offline action:', error);
                // Keep failed actions in queue for retry
            }
        }

        // Remove processed actions
        const remainingQueue = offlineQueue.filter(item => !processedIds.includes(item.id));
        localStorage.setItem('offlineQueue', JSON.stringify(remainingQueue));

        if (processedIds.length > 0) {
            window.loadingManager?.showToast(`Synced ${processedIds.length} offline actions`, 'success');
        }
    }

    async executeOfflineAction(item) {
        switch (item.action) {
            case 'deleteMeeting':
                await fetch(`/api/meetings/${item.data.meetingId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                break;
            case 'updateMeeting':
                await fetch(`/api/meetings/${item.data.meetingId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(item.data.updates)
                });
                break;
            // Add more offline actions as needed
        }
    }

    // Performance monitoring
    trackPerformance(action, startTime) {
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        console.log(`Performance: ${action} took ${duration.toFixed(2)}ms`);
        
        // Send performance data to analytics (if implemented)
        this.emit('performance:metric', {
            action,
            duration,
            timestamp: new Date().toISOString()
        });
    }

    // Cleanup
    destroy() {
        this.stopPolling();
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
        this.listeners.clear();
    }
}

// Create global instance
window.realtimeManager = new RealtimeManager();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RealtimeManager;
}
