/**
 * Global Loading Manager
 * Handles loading states, progress indicators, and performance optimizations
 */

class LoadingManager {
    constructor() {
        this.activeRequests = new Map();
        this.loadingStates = new Map();
        this.cache = new Map();
        this.cacheExpiry = new Map();
        this.defaultCacheDuration = 5 * 60 * 1000; // 5 minutes
        
        this.initializeLoadingElements();
        this.setupPerformanceMonitoring();
    }

    initializeLoadingElements() {
        // Create global loading overlay if it doesn't exist
        if (!document.getElementById('global-loading')) {
            const loadingOverlay = document.createElement('div');
            loadingOverlay.id = 'global-loading';
            loadingOverlay.className = 'loading-overlay';
            loadingOverlay.innerHTML = `
                <div class="loading-content">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Loading...</div>
                    <div class="loading-progress">
                        <div class="progress-bar">
                            <div class="progress-fill"></div>
                        </div>
                        <div class="progress-text">0%</div>
                    </div>
                </div>
            `;
            document.body.appendChild(loadingOverlay);
        }

        // Create toast container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            const toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
    }

    setupPerformanceMonitoring() {
        // Monitor page load performance
        if ('performance' in window) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    if (perfData) {
                        console.log('Page Load Performance:', {
                            loadTime: perfData.loadEventEnd - perfData.loadEventStart,
                            domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                            totalTime: perfData.loadEventEnd - perfData.fetchStart
                        });
                    }
                }, 0);
            });
        }
    }

    // Enhanced loading states
    showLoading(message = 'Loading...', options = {}) {
        const {
            showProgress = false,
            progress = 0,
            overlay = true,
            target = null,
            id = 'default'
        } = options;

        this.loadingStates.set(id, { message, progress, showProgress });

        if (target) {
            this.showTargetLoading(target, message, options);
        } else if (overlay) {
            this.showGlobalLoading(message, options);
        }
    }

    showGlobalLoading(message, options = {}) {
        const overlay = document.getElementById('global-loading');
        const textElement = overlay.querySelector('.loading-text');
        const progressContainer = overlay.querySelector('.loading-progress');
        const progressFill = overlay.querySelector('.progress-fill');
        const progressText = overlay.querySelector('.progress-text');

        if (textElement) textElement.textContent = message;
        
        if (options.showProgress) {
            progressContainer.style.display = 'block';
            this.updateProgress(options.progress || 0);
        } else {
            progressContainer.style.display = 'none';
        }

        overlay.classList.add('show');
    }

    showTargetLoading(target, message, options = {}) {
        const existingLoader = target.querySelector('.inline-loader');
        if (existingLoader) {
            existingLoader.remove();
        }

        const loader = document.createElement('div');
        loader.className = 'inline-loader';
        loader.innerHTML = `
            <div class="inline-spinner"></div>
            <span class="inline-text">${message}</span>
        `;

        if (options.position === 'prepend') {
            target.prepend(loader);
        } else {
            target.appendChild(loader);
        }
    }

    updateProgress(progress, id = 'default') {
        const state = this.loadingStates.get(id);
        if (state) {
            state.progress = progress;
            this.loadingStates.set(id, state);
        }

        const overlay = document.getElementById('global-loading');
        const progressFill = overlay.querySelector('.progress-fill');
        const progressText = overlay.querySelector('.progress-text');

        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
        if (progressText) {
            progressText.textContent = `${Math.round(progress)}%`;
        }
    }

    hideLoading(id = 'default', target = null) {
        this.loadingStates.delete(id);

        if (target) {
            const loader = target.querySelector('.inline-loader');
            if (loader) {
                loader.remove();
            }
        } else {
            const overlay = document.getElementById('global-loading');
            overlay.classList.remove('show');
        }
    }

    // Enhanced caching system
    setCache(key, data, duration = this.defaultCacheDuration) {
        this.cache.set(key, data);
        this.cacheExpiry.set(key, Date.now() + duration);
    }

    getCache(key) {
        const expiry = this.cacheExpiry.get(key);
        if (!expiry || Date.now() > expiry) {
            this.cache.delete(key);
            this.cacheExpiry.delete(key);
            return null;
        }
        return this.cache.get(key);
    }

    clearCache(pattern = null) {
        if (pattern) {
            for (const key of this.cache.keys()) {
                if (key.includes(pattern)) {
                    this.cache.delete(key);
                    this.cacheExpiry.delete(key);
                }
            }
        } else {
            this.cache.clear();
            this.cacheExpiry.clear();
        }
    }

    // Enhanced fetch with caching and loading states
    async fetchWithCache(url, options = {}) {
        const {
            cache = true,
            cacheDuration = this.defaultCacheDuration,
            loadingMessage = 'Loading...',
            showLoading = true,
            loadingId = url
        } = options;

        // Check cache first
        if (cache) {
            const cached = this.getCache(url);
            if (cached) {
                return cached;
            }
        }

        // Show loading state
        if (showLoading) {
            this.showLoading(loadingMessage, { id: loadingId });
        }

        try {
            // Track active request
            const controller = new AbortController();
            this.activeRequests.set(loadingId, controller);

            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            // Cache the result
            if (cache) {
                this.setCache(url, data, cacheDuration);
            }

            return data;

        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Fetch error:', error);
                this.showToast(`Error: ${error.message}`, 'error');
            }
            throw error;
        } finally {
            // Clean up
            this.activeRequests.delete(loadingId);
            if (showLoading) {
                this.hideLoading(loadingId);
            }
        }
    }

    // Cancel active requests
    cancelRequest(id) {
        const controller = this.activeRequests.get(id);
        if (controller) {
            controller.abort();
            this.activeRequests.delete(id);
        }
    }

    cancelAllRequests() {
        for (const [id, controller] of this.activeRequests) {
            controller.abort();
        }
        this.activeRequests.clear();
    }

    // Enhanced toast notifications
    showToast(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icon = this.getToastIcon(type);
        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-message">${message}</div>
            <button class="toast-close">&times;</button>
        `;

        container.appendChild(toast);

        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);

        // Auto hide
        const hideTimeout = setTimeout(() => {
            this.hideToast(toast);
        }, duration);

        // Manual close
        toast.querySelector('.toast-close').addEventListener('click', () => {
            clearTimeout(hideTimeout);
            this.hideToast(toast);
        });

        return toast;
    }

    hideToast(toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    getToastIcon(type) {
        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-exclamation-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            info: '<i class="fas fa-info-circle"></i>'
        };
        return icons[type] || icons.info;
    }

    // Performance utilities
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // Lazy loading for images
    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        observer.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }
}

// Create global instance
window.loadingManager = new LoadingManager();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoadingManager;
}
