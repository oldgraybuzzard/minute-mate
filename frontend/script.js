/**
 * MinuteMate Frontend JavaScript
 * Handles file upload, progress tracking, and user interactions
 */

class MinuteMateApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000';
        this.currentJobId = null;
        this.selectedFile = null;
        this.pollInterval = null;
        
        this.initializeElements();
        this.bindEvents();
        this.checkSystemHealth();
    }

    initializeElements() {
        // Upload elements
        this.uploadArea = document.getElementById('upload-area');
        this.fileInput = document.getElementById('file-input');
        this.fileInfo = document.getElementById('file-info');
        this.fileName = document.getElementById('file-name');
        this.fileSize = document.getElementById('file-size');
        this.removeFileBtn = document.getElementById('remove-file');
        this.uploadBtn = document.getElementById('upload-btn');
        this.languageSelect = document.getElementById('language-select');
        this.formatSelect = document.getElementById('format-select');

        // Processing elements
        this.jobId = document.getElementById('job-id');
        this.processingFilename = document.getElementById('processing-filename');
        this.processingFilesize = document.getElementById('processing-filesize');
        this.progressFill = document.getElementById('progress-fill');
        this.progressPercentage = document.getElementById('progress-percentage');
        this.progressStage = document.getElementById('progress-stage');
        this.cancelBtn = document.getElementById('cancel-btn');

        // Results elements
        this.processingTime = document.getElementById('processing-time');
        this.attendeesCount = document.getElementById('attendees-count');
        this.motionsCount = document.getElementById('motions-count');
        this.downloadDocxBtn = document.getElementById('download-docx');
        this.downloadPdfBtn = document.getElementById('download-pdf');
        this.viewPreviewBtn = document.getElementById('view-preview');

        // Error elements
        this.errorText = document.getElementById('error-text');
        this.errorId = document.getElementById('error-id');
        this.retryBtn = document.getElementById('retry-btn');

        // Navigation elements
        this.newUploadBtns = document.querySelectorAll('.new-upload-btn, #error-new-upload-btn');

        // Sections
        this.sections = {
            upload: document.getElementById('upload-section'),
            processing: document.getElementById('processing-section'),
            results: document.getElementById('results-section'),
            error: document.getElementById('error-section')
        };

        // Processing steps
        this.steps = {
            upload: document.getElementById('step-upload'),
            transcription: document.getElementById('step-transcription'),
            parsing: document.getElementById('step-parsing'),
            formatting: document.getElementById('step-formatting')
        };

        // Utility elements
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.toast = document.getElementById('toast');
        this.healthCheckBtn = document.getElementById('health-check');
    }

    bindEvents() {
        // File upload events
        this.uploadArea.addEventListener('click', () => this.fileInput.click());
        this.uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        this.uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        this.removeFileBtn.addEventListener('click', this.removeFile.bind(this));
        this.uploadBtn.addEventListener('click', this.startUpload.bind(this));

        // Processing events
        this.cancelBtn.addEventListener('click', this.cancelProcessing.bind(this));

        // Results events
        this.downloadDocxBtn.addEventListener('click', () => this.downloadFile('docx'));
        this.downloadPdfBtn.addEventListener('click', () => this.downloadFile('pdf'));
        this.viewPreviewBtn.addEventListener('click', this.viewPreview.bind(this));

        // Error events
        this.retryBtn.addEventListener('click', this.retryProcessing.bind(this));

        // Navigation events
        this.newUploadBtns.forEach(btn => {
            btn.addEventListener('click', this.resetToUpload.bind(this));
        });

        // Utility events
        this.healthCheckBtn.addEventListener('click', this.showSystemHealth.bind(this));

        // Prevent default drag behaviors
        document.addEventListener('dragover', e => e.preventDefault());
        document.addEventListener('drop', e => e.preventDefault());
    }

    // File handling methods
    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.selectFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.selectFile(files[0]);
        }
    }

    selectFile(file) {
        // Validate file type
        const allowedTypes = [
            'audio/mpeg', 'audio/wav', 'audio/flac', 'audio/mp4', 'audio/aac', 'audio/ogg',
            'video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo'
        ];

        if (!allowedTypes.includes(file.type) && !this.isValidFileExtension(file.name)) {
            this.showToast('Invalid file type. Please select an audio or video file.', 'error');
            return;
        }

        // Validate file size (500MB limit)
        const maxSize = 500 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showToast('File too large. Maximum size is 500MB.', 'error');
            return;
        }

        this.selectedFile = file;
        this.displayFileInfo(file);
        this.uploadBtn.disabled = false;
    }

    isValidFileExtension(filename) {
        const validExtensions = [
            '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma',
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'
        ];
        
        const extension = filename.toLowerCase().substring(filename.lastIndexOf('.'));
        return validExtensions.includes(extension);
    }

    displayFileInfo(file) {
        this.fileName.textContent = file.name;
        this.fileSize.textContent = this.formatFileSize(file.size);
        this.fileInfo.style.display = 'block';
        this.uploadArea.style.display = 'none';
    }

    removeFile() {
        this.selectedFile = null;
        this.fileInfo.style.display = 'none';
        this.uploadArea.style.display = 'block';
        this.uploadBtn.disabled = true;
        this.fileInput.value = '';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Upload and processing methods
    async startUpload() {
        if (!this.selectedFile) {
            this.showToast('Please select a file first.', 'error');
            return;
        }

        this.showLoading('Uploading file...');

        try {
            const formData = new FormData();
            formData.append('file', this.selectedFile);

            const response = await fetch(`${this.apiBaseUrl}/api/upload`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.currentJobId = result.data.job_id;
                this.showProcessingSection(result.data);
                this.startPolling();
            } else {
                throw new Error(result.message || 'Upload failed');
            }
        } catch (error) {
            this.showError('Upload failed: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    showProcessingSection(data) {
        this.jobId.textContent = data.job_id;
        this.processingFilename.textContent = data.filename;
        this.processingFilesize.textContent = data.file_size;
        
        this.showSection('processing');
        this.updateStep('upload', 'active');
        this.updateProgress(10, 'File uploaded successfully');
    }

    async startPolling() {
        this.pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiBaseUrl}/api/status/${this.currentJobId}`);
                const result = await response.json();

                if (result.success) {
                    this.updateProcessingStatus(result.data);
                } else {
                    this.stopPolling();
                    this.showError('Failed to get job status: ' + result.message);
                }
            } catch (error) {
                console.error('Polling error:', error);
                // Continue polling unless it's a critical error
            }
        }, 2000); // Poll every 2 seconds
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    updateProcessingStatus(jobData) {
        const status = jobData.status;
        const progress = jobData.progress || 0;
        const message = jobData.message || '';

        this.updateProgress(progress, message);

        // Update steps based on status
        switch (status) {
            case 'uploaded':
                this.updateStep('upload', 'completed');
                break;
            case 'transcribing':
                this.updateStep('upload', 'completed');
                this.updateStep('transcription', 'active');
                break;
            case 'parsing':
                this.updateStep('upload', 'completed');
                this.updateStep('transcription', 'completed');
                this.updateStep('parsing', 'active');
                break;
            case 'formatting':
                this.updateStep('upload', 'completed');
                this.updateStep('transcription', 'completed');
                this.updateStep('parsing', 'completed');
                this.updateStep('formatting', 'active');
                break;
            case 'completed':
                this.stopPolling();
                this.updateStep('upload', 'completed');
                this.updateStep('transcription', 'completed');
                this.updateStep('parsing', 'completed');
                this.updateStep('formatting', 'completed');
                this.updateProgress(100, 'Processing complete!');
                setTimeout(() => this.showResults(jobData), 1000);
                break;
            case 'failed':
                this.stopPolling();
                this.updateStep('upload', 'error');
                this.showError(jobData.error || 'Processing failed', jobData.error_id);
                break;
        }
    }

    updateProgress(percentage, message) {
        this.progressFill.style.width = `${percentage}%`;
        this.progressPercentage.textContent = `${percentage}%`;
        this.progressStage.textContent = message;
    }

    updateStep(stepName, status) {
        const step = this.steps[stepName];
        if (!step) return;

        // Remove all status classes
        step.classList.remove('active', 'completed', 'error');
        
        // Add new status class
        step.classList.add(status);

        // Update step status icon
        const statusIcon = step.querySelector('.step-status i');
        statusIcon.className = this.getStepIcon(status);
    }

    getStepIcon(status) {
        switch (status) {
            case 'active':
                return 'fas fa-spinner fa-spin';
            case 'completed':
                return 'fas fa-check';
            case 'error':
                return 'fas fa-times';
            default:
                return 'fas fa-clock';
        }
    }

    async cancelProcessing() {
        if (confirm('Are you sure you want to cancel processing?')) {
            this.stopPolling();
            this.resetToUpload();
            this.showToast('Processing cancelled', 'warning');
        }
    }

    showResults(jobData) {
        // Mock data for demonstration - in real implementation, this would come from the API
        this.processingTime.textContent = '2m 34s';
        this.attendeesCount.textContent = '8';
        this.motionsCount.textContent = '3';
        
        this.showSection('results');
    }

    async downloadFile(format) {
        if (!this.currentJobId) {
            this.showToast('No job ID available for download', 'error');
            return;
        }

        try {
            this.showLoading(`Preparing ${format.toUpperCase()} download...`);
            
            const response = await fetch(`${this.apiBaseUrl}/api/download/${this.currentJobId}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `meeting-minutes-${this.currentJobId}.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showToast(`${format.toUpperCase()} downloaded successfully!`, 'success');
            } else {
                const result = await response.json();
                throw new Error(result.message || 'Download failed');
            }
        } catch (error) {
            this.showToast('Download failed: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    viewPreview() {
        // In a real implementation, this would open a modal or new window with the preview
        this.showToast('Preview feature coming soon!', 'warning');
    }

    retryProcessing() {
        if (this.selectedFile) {
            this.startUpload();
        } else {
            this.resetToUpload();
        }
    }

    resetToUpload() {
        this.stopPolling();
        this.currentJobId = null;
        this.removeFile();
        this.showSection('upload');
        
        // Reset all steps
        Object.values(this.steps).forEach(step => {
            step.classList.remove('active', 'completed', 'error');
            const statusIcon = step.querySelector('.step-status i');
            statusIcon.className = 'fas fa-clock';
        });
        
        // Reset progress
        this.updateProgress(0, 'Ready to upload');
    }

    // UI utility methods
    showSection(sectionName) {
        Object.values(this.sections).forEach(section => {
            section.classList.remove('active');
        });
        
        if (this.sections[sectionName]) {
            this.sections[sectionName].classList.add('active');
        }
    }

    showError(message, errorId = null) {
        this.errorText.textContent = message;
        this.errorId.textContent = errorId || 'N/A';
        this.showSection('error');
    }

    showLoading(message = 'Loading...') {
        this.loadingOverlay.querySelector('p').textContent = message;
        this.loadingOverlay.classList.add('show');
    }

    hideLoading() {
        this.loadingOverlay.classList.remove('show');
    }

    showToast(message, type = 'info') {
        const toast = this.toast;
        const icon = toast.querySelector('.toast-icon');
        const messageEl = toast.querySelector('.toast-message');
        
        // Set message
        messageEl.textContent = message;
        
        // Set icon and type
        toast.className = `toast ${type}`;
        switch (type) {
            case 'success':
                icon.className = 'toast-icon fas fa-check-circle';
                break;
            case 'error':
                icon.className = 'toast-icon fas fa-exclamation-circle';
                break;
            case 'warning':
                icon.className = 'toast-icon fas fa-exclamation-triangle';
                break;
            default:
                icon.className = 'toast-icon fas fa-info-circle';
        }
        
        // Show toast
        toast.classList.add('show');
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            toast.classList.remove('show');
        }, 5000);
    }

    async checkSystemHealth() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/`);
            if (response.ok) {
                console.log('System health check passed');
            } else {
                console.warn('System health check failed');
            }
        } catch (error) {
            console.error('System health check error:', error);
            this.showToast('Unable to connect to server. Please check your connection.', 'error');
        }
    }

    async showSystemHealth() {
        try {
            this.showLoading('Checking system health...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/health/detailed`);
            const result = await response.json();
            
            if (response.ok) {
                const health = result;
                const message = `System Status: ${health.status}\nUptime: ${Math.round(health.uptime_seconds / 60)} minutes\nTotal Requests: ${health.requests_total}\nError Rate: ${(health.error_rate * 100).toFixed(2)}%`;
                alert(message);
            } else {
                throw new Error('Health check failed');
            }
        } catch (error) {
            this.showToast('Failed to get system health: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MinuteMateApp();
});
