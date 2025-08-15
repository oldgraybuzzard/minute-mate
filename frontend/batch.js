/**
 * MinuteMate Batch Processing JavaScript
 * Handles batch upload, processing, and management
 */

class BatchApp {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.currentUser = null;
        this.selectedFiles = [];
        this.templates = [];
        this.batchJobs = [];
        this.refreshInterval = null;
        
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
        
        // Batch elements
        this.newBatchBtn = document.getElementById('new-batch-btn');
        this.viewStatsBtn = document.getElementById('view-stats-btn');
        this.batchUploadSection = document.getElementById('batch-upload-section');
        this.closeUploadBtn = document.getElementById('close-upload-btn');
        this.batchUploadForm = document.getElementById('batch-upload-form');
        this.batchJobsList = document.getElementById('batch-jobs-list');
        this.statusFilter = document.getElementById('status-filter');
        
        // Upload elements
        this.uploadZone = document.getElementById('upload-zone');
        this.fileInput = document.getElementById('file-input');
        this.browseFilesBtn = document.getElementById('browse-files');
        this.fileList = document.getElementById('file-list');
        this.filesContainer = document.getElementById('files-container');
        this.fileCount = document.getElementById('file-count');
        this.totalSize = document.getElementById('total-size');
        this.createBatchBtn = document.getElementById('create-batch');
        this.cancelBatchBtn = document.getElementById('cancel-batch');
        
        // Template elements
        this.batchTemplate = document.getElementById('batch-template');
        this.generateDocuments = document.getElementById('generate-documents');
        this.documentFormatsGroup = document.getElementById('document-formats-group');
        
        // Modal elements
        this.statsModal = document.getElementById('stats-modal');
        this.statsContent = document.getElementById('stats-content');
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

        // Batch actions
        this.newBatchBtn.addEventListener('click', () => this.showUploadSection());
        this.viewStatsBtn.addEventListener('click', () => this.showStatistics());
        this.closeUploadBtn.addEventListener('click', () => this.hideUploadSection());
        this.cancelBatchBtn.addEventListener('click', () => this.hideUploadSection());
        
        // Upload actions
        this.browseFilesBtn.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelection(e));
        this.batchUploadForm.addEventListener('submit', this.createBatch.bind(this));
        
        // Drag and drop
        this.uploadZone.addEventListener('dragover', this.handleDragOver.bind(this));
        this.uploadZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.uploadZone.addEventListener('drop', this.handleDrop.bind(this));
        
        // Document generation toggle
        this.generateDocuments.addEventListener('change', (e) => {
            this.documentFormatsGroup.style.display = e.target.checked ? 'block' : 'none';
        });
        
        // Filter
        this.statusFilter.addEventListener('change', () => this.filterBatchJobs());
        
        // Modal actions
        this.statsModal.querySelector('.stats-modal-close').addEventListener('click', () => this.closeStatsModal());
        document.getElementById('cancel-confirmation').addEventListener('click', () => this.closeConfirmationModal());
        
        // Close modals when clicking outside
        [this.statsModal, this.confirmationModal].forEach(modal => {
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
            this.loadTemplates();
            this.loadBatchJobs();
            this.startRefreshInterval();
            
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

    async loadTemplates() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/templates/`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.templates = result.data.templates;
                    this.populateTemplateSelect();
                }
            }
        } catch (error) {
            console.error('Failed to load templates:', error);
        }
    }

    populateTemplateSelect() {
        this.batchTemplate.innerHTML = '<option value="">No template</option>';
        
        this.templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            this.batchTemplate.appendChild(option);
        });
    }

    async loadBatchJobs() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/batch/`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.batchJobs = result.data.batches;
                    this.renderBatchJobs();
                } else {
                    throw new Error(result.message);
                }
            } else {
                throw new Error('Failed to load batch jobs');
            }
        } catch (error) {
            console.error('Batch jobs load error:', error);
            this.batchJobsList.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Failed to load batch jobs</h3>
                    <p>Please try refreshing the page</p>
                </div>
            `;
        }
    }

    renderBatchJobs() {
        if (!this.batchJobs || this.batchJobs.length === 0) {
            this.batchJobsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-layer-group"></i>
                    <h3>No batch jobs yet</h3>
                    <p>Create your first batch to process multiple recordings at once!</p>
                    <button class="btn primary" onclick="batchApp.showUploadSection()">
                        <i class="fas fa-plus"></i> Create Batch
                    </button>
                </div>
            `;
            return;
        }

        const batchesHtml = this.batchJobs.map(batch => this.renderBatchCard(batch)).join('');
        this.batchJobsList.innerHTML = batchesHtml;
    }

    renderBatchCard(batch) {
        const statusClass = this.getStatusClass(batch.status);
        const progressPercentage = batch.progress_percentage || 0;
        
        return `
            <div class="batch-card" data-batch-id="${batch.id}">
                <div class="batch-header">
                    <div class="batch-info">
                        <h4>${batch.name}</h4>
                        <p class="batch-description">${batch.description || 'No description'}</p>
                    </div>
                    <div class="batch-status">
                        <span class="status-badge status-${statusClass}">${batch.status}</span>
                    </div>
                </div>
                
                <div class="batch-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progressPercentage}%"></div>
                    </div>
                    <div class="progress-text">${progressPercentage}% complete</div>
                </div>
                
                <div class="batch-stats">
                    <div class="stat-item">
                        <strong>Total:</strong> ${batch.total_files}
                    </div>
                    <div class="stat-item">
                        <strong>Processed:</strong> ${batch.processed_files}
                    </div>
                    <div class="stat-item">
                        <strong>Failed:</strong> ${batch.failed_files}
                    </div>
                    <div class="stat-item">
                        <strong>Created:</strong> ${new Date(batch.created_at).toLocaleDateString()}
                    </div>
                </div>
                
                ${batch.error_message ? `
                    <div class="error-message">
                        <i class="fas fa-exclamation-triangle"></i>
                        ${batch.error_message}
                    </div>
                ` : ''}
                
                <div class="batch-actions">
                    ${this.getBatchActions(batch)}
                </div>
            </div>
        `;
    }

    getBatchActions(batch) {
        const actions = [];
        
        switch (batch.status) {
            case 'uploaded':
                actions.push(`<button class="btn-small primary" onclick="batchApp.startBatch('${batch.id}')">
                    <i class="fas fa-play"></i> Start
                </button>`);
                break;
            case 'processing':
                actions.push(`<button class="btn-small warning" onclick="batchApp.cancelBatch('${batch.id}')">
                    <i class="fas fa-stop"></i> Cancel
                </button>`);
                break;
            case 'completed':
            case 'partial':
                actions.push(`<button class="btn-small success" onclick="batchApp.downloadBatch('${batch.id}')">
                    <i class="fas fa-download"></i> Download
                </button>`);
                if (batch.failed_files > 0) {
                    actions.push(`<button class="btn-small secondary" onclick="batchApp.retryBatch('${batch.id}')">
                        <i class="fas fa-redo"></i> Retry Failed
                    </button>`);
                }
                break;
            case 'failed':
                actions.push(`<button class="btn-small secondary" onclick="batchApp.retryBatch('${batch.id}')">
                    <i class="fas fa-redo"></i> Retry
                </button>`);
                break;
        }
        
        actions.push(`<button class="btn-small danger" onclick="batchApp.deleteBatch('${batch.id}')">
            <i class="fas fa-trash"></i> Delete
        </button>`);
        
        return actions.join('');
    }

    getStatusClass(status) {
        const statusMap = {
            'created': 'info',
            'uploaded': 'info',
            'processing': 'warning',
            'completed': 'success',
            'failed': 'danger',
            'partial': 'warning',
            'cancelled': 'secondary'
        };
        return statusMap[status] || 'info';
    }

    showUploadSection() {
        this.batchUploadSection.style.display = 'block';
        this.batchUploadSection.scrollIntoView({ behavior: 'smooth' });
    }

    hideUploadSection() {
        this.batchUploadSection.style.display = 'none';
        this.resetUploadForm();
    }

    resetUploadForm() {
        this.batchUploadForm.reset();
        this.selectedFiles = [];
        this.fileList.style.display = 'none';
        this.createBatchBtn.disabled = true;
        this.updateFileDisplay();
    }

    handleDragOver(e) {
        e.preventDefault();
        this.uploadZone.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.uploadZone.classList.remove('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        this.uploadZone.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files);
        this.addFiles(files);
    }

    handleFileSelection(e) {
        const files = Array.from(e.target.files);
        this.addFiles(files);
    }

    addFiles(files) {
        const validFiles = files.filter(file => this.validateFile(file));
        
        // Add to selected files (avoid duplicates)
        validFiles.forEach(file => {
            const exists = this.selectedFiles.some(f => f.name === file.name && f.size === file.size);
            if (!exists) {
                this.selectedFiles.push(file);
            }
        });
        
        this.updateFileDisplay();
        this.createBatchBtn.disabled = this.selectedFiles.length === 0;
    }

    validateFile(file) {
        const maxSize = 100 * 1024 * 1024; // 100MB
        const allowedTypes = ['audio/', 'video/'];
        const allowedExtensions = ['.mp3', '.mp4', '.wav', '.m4a', '.webm'];
        
        if (file.size > maxSize) {
            this.showToast(`File ${file.name} is too large (max 100MB)`, 'error');
            return false;
        }
        
        const isValidType = allowedTypes.some(type => file.type.startsWith(type)) ||
                           allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
        
        if (!isValidType) {
            this.showToast(`File ${file.name} is not a supported format`, 'error');
            return false;
        }
        
        return true;
    }

    updateFileDisplay() {
        if (this.selectedFiles.length === 0) {
            this.fileList.style.display = 'none';
            return;
        }
        
        this.fileList.style.display = 'block';
        
        const filesHtml = this.selectedFiles.map((file, index) => `
            <div class="file-item">
                <div class="file-info">
                    <i class="fas fa-file-audio"></i>
                    <span class="file-name">${file.name}</span>
                    <span class="file-size">${this.formatFileSize(file.size)}</span>
                </div>
                <button type="button" class="remove-file" onclick="batchApp.removeFile(${index})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
        
        this.filesContainer.innerHTML = filesHtml;
        
        const totalSize = this.selectedFiles.reduce((sum, file) => sum + file.size, 0);
        this.fileCount.textContent = `${this.selectedFiles.length} files`;
        this.totalSize.textContent = this.formatFileSize(totalSize);
        
        // Check total size limit
        const maxBatchSize = 500 * 1024 * 1024; // 500MB
        if (totalSize > maxBatchSize) {
            this.showToast('Total batch size exceeds 500MB limit', 'error');
            this.createBatchBtn.disabled = true;
        }
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.updateFileDisplay();
        this.createBatchBtn.disabled = this.selectedFiles.length === 0;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    async createBatch(e) {
        e.preventDefault();
        
        if (this.selectedFiles.length === 0) {
            this.showToast('Please select files to upload', 'error');
            return;
        }
        
        try {
            this.showLoading('Creating batch job...');
            
            const formData = new FormData(this.batchUploadForm);
            
            // Add files to form data
            this.selectedFiles.forEach(file => {
                formData.append('files', file);
            });
            
            // Add document formats
            const documentFormats = Array.from(document.querySelectorAll('input[name="document_formats"]:checked'))
                                         .map(cb => cb.value);
            documentFormats.forEach(format => {
                formData.append('document_formats', format);
            });
            
            const response = await fetch(`${this.apiBaseUrl}/api/batch/upload`, {
                method: 'POST',
                credentials: 'include',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Batch created successfully!', 'success');
                this.hideUploadSection();
                this.loadBatchJobs();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Create batch error:', error);
            this.showToast('Failed to create batch', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async startBatch(batchId) {
        try {
            this.showLoading('Starting batch processing...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/batch/${batchId}/start`, {
                method: 'POST',
                credentials: 'include'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Batch processing started', 'success');
                this.loadBatchJobs();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Start batch error:', error);
            this.showToast('Failed to start batch', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async cancelBatch(batchId) {
        this.confirmationMessage.textContent = 'Are you sure you want to cancel this batch job?';
        this.confirmActionBtn.onclick = () => this.confirmCancelBatch(batchId);
        this.confirmationModal.classList.add('show');
    }

    async confirmCancelBatch(batchId) {
        try {
            this.closeConfirmationModal();
            this.showLoading('Cancelling batch...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/batch/${batchId}/cancel`, {
                method: 'POST',
                credentials: 'include'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Batch cancelled', 'success');
                this.loadBatchJobs();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Cancel batch error:', error);
            this.showToast('Failed to cancel batch', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async retryBatch(batchId) {
        try {
            this.showLoading('Retrying failed files...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/batch/${batchId}/retry`, {
                method: 'POST',
                credentials: 'include'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast(`Retrying ${result.data.retry_count} failed files`, 'success');
                this.loadBatchJobs();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Retry batch error:', error);
            this.showToast('Failed to retry batch', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async downloadBatch(batchId) {
        try {
            this.showLoading('Preparing download...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/batch/${batchId}/download`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `batch_${batchId}_results.zip`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showToast('Download started', 'success');
            } else {
                const result = await response.json();
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Download batch error:', error);
            this.showToast('Failed to download batch results', 'error');
        } finally {
            this.hideLoading();
        }
    }

    deleteBatch(batchId) {
        this.confirmationMessage.textContent = 'Are you sure you want to delete this batch job? This action cannot be undone.';
        this.confirmActionBtn.onclick = () => this.confirmDeleteBatch(batchId);
        this.confirmationModal.classList.add('show');
    }

    async confirmDeleteBatch(batchId) {
        try {
            this.closeConfirmationModal();
            this.showLoading('Deleting batch...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/batch/${batchId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Batch deleted successfully', 'success');
                this.loadBatchJobs();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Delete batch error:', error);
            this.showToast('Failed to delete batch', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async showStatistics() {
        try {
            this.showLoading('Loading statistics...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/batch/stats`, {
                credentials: 'include'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.renderStatistics(result.data.stats);
                this.statsModal.classList.add('show');
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Load statistics error:', error);
            this.showToast('Failed to load statistics', 'error');
        } finally {
            this.hideLoading();
        }
    }

    renderStatistics(stats) {
        const statusCounts = stats.status_counts || {};
        const recentBatches = stats.recent_batches || [];
        
        this.statsContent.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <h4>Total Batches</h4>
                    <div class="stat-value">${stats.total_batches}</div>
                </div>
                <div class="stat-card">
                    <h4>Files Processed</h4>
                    <div class="stat-value">${stats.total_files_processed}</div>
                </div>
                <div class="stat-card">
                    <h4>Files Failed</h4>
                    <div class="stat-value">${stats.total_files_failed}</div>
                </div>
                <div class="stat-card">
                    <h4>Success Rate</h4>
                    <div class="stat-value">${this.calculateSuccessRate(stats)}%</div>
                </div>
            </div>
            
            <div class="status-breakdown">
                <h4>Status Breakdown</h4>
                <div class="status-list">
                    ${Object.entries(statusCounts).map(([status, count]) => `
                        <div class="status-item">
                            <span class="status-badge status-${this.getStatusClass(status)}">${status}</span>
                            <span class="status-count">${count}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            ${recentBatches.length > 0 ? `
                <div class="recent-batches">
                    <h4>Recent Batches</h4>
                    <div class="recent-list">
                        ${recentBatches.map(batch => `
                            <div class="recent-item">
                                <span class="batch-name">${batch.name}</span>
                                <span class="batch-date">${new Date(batch.created_at).toLocaleDateString()}</span>
                                <span class="status-badge status-${this.getStatusClass(batch.status)}">${batch.status}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;
    }

    calculateSuccessRate(stats) {
        const total = stats.total_files_processed + stats.total_files_failed;
        if (total === 0) return 100;
        return Math.round((stats.total_files_processed / total) * 100);
    }

    filterBatchJobs() {
        const statusFilter = this.statusFilter.value;
        
        if (!statusFilter) {
            this.renderBatchJobs();
            return;
        }
        
        const filteredBatches = this.batchJobs.filter(batch => batch.status === statusFilter);
        const originalBatches = this.batchJobs;
        this.batchJobs = filteredBatches;
        this.renderBatchJobs();
        this.batchJobs = originalBatches;
    }

    startRefreshInterval() {
        // Refresh batch jobs every 5 seconds if there are active batches
        this.refreshInterval = setInterval(() => {
            const hasActiveBatches = this.batchJobs.some(batch => 
                ['processing', 'uploaded'].includes(batch.status)
            );
            
            if (hasActiveBatches) {
                this.loadBatchJobs();
            }
        }, 5000);
    }

    closeStatsModal() {
        this.statsModal.classList.remove('show');
    }

    closeConfirmationModal() {
        this.confirmationModal.classList.remove('show');
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
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
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

// Initialize the batch app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.batchApp = new BatchApp();
});
