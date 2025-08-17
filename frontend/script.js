/**
 * MinuteMate Frontend JavaScript
 * Handles file upload, progress tracking, and user interactions
 */

class MinuteMateApp {
    constructor() {
        // API base URL - backend runs on port 5000
        this.apiBaseUrl = 'http://localhost:5000';
        this.currentJobId = null;
        this.selectedFile = null;
        this.pollInterval = null;
        
        this.initializeElements();
        this.bindEvents();
        this.checkSystemHealth();
        this.loadUserPreferences();
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

        // Upload method elements
        this.fileMethodBtn = document.getElementById('file-method-btn');
        this.urlMethodBtn = document.getElementById('url-method-btn');
        this.transcriptMethodBtn = document.getElementById('transcript-method-btn');
        this.urlUploadArea = document.getElementById('url-upload-area');
        this.transcriptUploadArea = document.getElementById('transcript-upload-area');
        this.urlInput = document.getElementById('url-input');
        this.urlValidateBtn = document.getElementById('url-validate-btn');
        this.urlFilenameInput = document.getElementById('url-filename');
        this.urlFilenameGroup = document.querySelector('.url-filename-group');

        // Transcript elements
        this.transcriptUploadArea = document.getElementById('transcript-upload-area');
        this.transcriptFileUploadArea = document.querySelector('.transcript-file-upload .upload-area');
        this.transcriptFileInput = document.getElementById('transcript-file-input');
        this.transcriptText = document.getElementById('transcript-text');
        this.clearTranscriptBtn = document.getElementById('clear-transcript-btn');
        this.processTranscriptBtn = document.getElementById('process-transcript-btn');

        // Current upload method and data
        this.uploadMethod = 'file'; // 'file', 'url', or 'transcript'
        this.validatedUrl = null;
        this.transcriptContent = null;

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
        this.downloadPrimaryBtn = document.getElementById('download-primary');
        this.downloadHtmlBtn = document.getElementById('download-html');
        this.downloadJsonBtn = document.getElementById('download-json');
        this.viewPreviewBtn = document.getElementById('view-preview');
        this.reviewBtn = document.getElementById('review-btn');
        this.themeToggle = document.getElementById('theme-toggle');

        // User menu elements
        this.userMenu = document.getElementById('user-menu');
        this.userMenuToggle = document.getElementById('user-menu-toggle');
        this.userDropdown = document.getElementById('user-dropdown');
        this.userName = document.getElementById('user-name');
        this.userFullName = document.getElementById('user-full-name');
        this.userEmail = document.getElementById('user-email');
        this.userLogout = document.getElementById('user-logout');

        // Error elements
        this.errorText = document.getElementById('error-text');
        this.errorId = document.getElementById('error-id');
        this.retryBtn = document.getElementById('retry-btn');

        // Navigation elements
        this.newUploadBtns = document.querySelectorAll('.new-upload-btn, #error-new-upload-btn');

        // Sections - filter out null elements to prevent errors on different pages
        const allSections = {
            upload: document.getElementById('upload-section'),
            processing: document.getElementById('processing-section'),
            results: document.getElementById('results-section'),
            error: document.getElementById('error-section'),
            dashboard: document.getElementById('dashboard-section'),
            templates: document.getElementById('templates-section'),
            profile: document.getElementById('profile-section'),
            settings: document.getElementById('settings-section')
        };

        // Only include sections that actually exist on this page
        this.sections = {};
        Object.keys(allSections).forEach(key => {
            if (allSections[key]) {
                this.sections[key] = allSections[key];
            }
        });

        // Processing steps - filter out null elements to prevent errors on different pages
        const allSteps = {
            upload: document.getElementById('step-upload'),
            transcription: document.getElementById('step-transcription'),
            parsing: document.getElementById('step-parsing'),
            formatting: document.getElementById('step-formatting')
        };

        // Only include steps that actually exist on this page
        this.steps = {};
        Object.keys(allSteps).forEach(key => {
            if (allSteps[key]) {
                this.steps[key] = allSteps[key];
            }
        });

        // Utility elements
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.toast = document.getElementById('toast');
        this.healthCheckBtn = document.getElementById('health-check');
    }

    bindEvents() {
        // Upload method selection events
        this.fileMethodBtn.addEventListener('click', () => this.switchUploadMethod('file'));
        this.urlMethodBtn.addEventListener('click', () => this.switchUploadMethod('url'));
        this.transcriptMethodBtn.addEventListener('click', () => this.switchUploadMethod('transcript'));

        // File upload events
        this.uploadArea.addEventListener('click', () => this.fileInput.click());
        this.uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        this.uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        this.removeFileBtn.addEventListener('click', this.removeFile.bind(this));

        // URL upload events
        this.urlInput.addEventListener('input', this.handleUrlInput.bind(this));
        this.urlValidateBtn.addEventListener('click', this.validateUrl.bind(this));
        this.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.validateUrl();
            }
        });

        // Transcript upload events
        this.transcriptFileUploadArea.addEventListener('click', () => this.transcriptFileInput.click());
        this.transcriptFileUploadArea.addEventListener('dragover', this.handleTranscriptDragOver.bind(this));
        this.transcriptFileUploadArea.addEventListener('dragleave', this.handleTranscriptDragLeave.bind(this));
        this.transcriptFileUploadArea.addEventListener('drop', this.handleTranscriptDrop.bind(this));
        this.transcriptFileInput.addEventListener('change', this.handleTranscriptFileSelect.bind(this));
        this.transcriptText.addEventListener('input', this.handleTranscriptTextInput.bind(this));
        this.clearTranscriptBtn.addEventListener('click', this.clearTranscript.bind(this));
        this.processTranscriptBtn.addEventListener('click', this.processTranscript.bind(this));

        // Upload button event (handles both file and URL)
        this.uploadBtn.addEventListener('click', this.startUpload.bind(this));

        // Processing events
        this.cancelBtn.addEventListener('click', this.cancelProcessing.bind(this));

        // Results events
        this.downloadPrimaryBtn.addEventListener('click', () => this.downloadFile('primary'));
        this.downloadHtmlBtn.addEventListener('click', () => this.downloadFile('html'));
        this.downloadJsonBtn.addEventListener('click', () => this.downloadFile('json'));
        this.viewPreviewBtn.addEventListener('click', this.viewPreview.bind(this));
        this.reviewBtn.addEventListener('click', this.showReviewModal.bind(this));

        // Theme toggle
        this.themeToggle.addEventListener('click', this.toggleTheme.bind(this));

        // User menu events
        if (this.userMenuToggle) {
            this.userMenuToggle.addEventListener('click', () => {
                this.userDropdown.classList.toggle('show');
            });
        }

        if (this.userLogout) {
            this.userLogout.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (this.userMenuToggle && this.userDropdown &&
                !this.userMenuToggle.contains(e.target) &&
                !this.userDropdown.contains(e.target)) {
                this.userDropdown.classList.remove('show');
            }
        });

        // Error events
        this.retryBtn.addEventListener('click', this.retryProcessing.bind(this));

        // Initialize theme
        this.initializeTheme();

        // Initialize logo
        this.initializeLogo();

        // Check authentication
        this.checkAuthentication();

        // Navigation handled by multi-page architecture

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

    // Upload method switching
    switchUploadMethod(method) {
        this.uploadMethod = method;

        // Update button states
        this.fileMethodBtn.classList.toggle('active', method === 'file');
        this.urlMethodBtn.classList.toggle('active', method === 'url');
        this.transcriptMethodBtn.classList.toggle('active', method === 'transcript');

        // Show/hide appropriate upload areas
        this.uploadArea.style.display = method === 'file' ? 'block' : 'none';
        this.urlUploadArea.style.display = method === 'url' ? 'block' : 'none';
        this.transcriptUploadArea.style.display = method === 'transcript' ? 'block' : 'none';

        // Reset states
        this.removeFile();
        this.resetUrlForm();
        this.resetTranscriptForm();
        this.uploadBtn.disabled = true;
    }

    // URL upload methods
    handleUrlInput() {
        const url = this.urlInput.value.trim();

        // Reset validation state
        this.urlInput.classList.remove('valid', 'error');
        this.validatedUrl = null;
        this.urlFilenameGroup.style.display = 'none';
        this.uploadBtn.disabled = true;

        // Enable validate button if URL looks valid
        this.urlValidateBtn.disabled = !url || !this.isValidUrlFormat(url);
    }

    isValidUrlFormat(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
        } catch {
            return false;
        }
    }

    async validateUrl() {
        const url = this.urlInput.value.trim();

        if (!url || !this.isValidUrlFormat(url)) {
            this.showToast('Please enter a valid URL', 'error');
            return;
        }

        // Check for streaming platforms
        if (this.isStreamingPlatform(url)) {
            this.urlInput.classList.add('error');
            this.urlInput.classList.remove('valid');
            this.showToast('Streaming platforms (YouTube, Vimeo, etc.) are not supported. Please use a direct download link.', 'error');
            return;
        }

        this.urlValidateBtn.disabled = true;
        this.urlValidateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Validating...';

        try {
            // Simple validation - try to fetch headers
            const response = await fetch(url, {
                method: 'HEAD',
                mode: 'no-cors' // This will limit what we can check, but avoids CORS issues
            });

            // Since we're using no-cors, we can't check the actual response
            // But if we get here without an error, the URL is at least reachable
            this.urlInput.classList.add('valid');
            this.urlInput.classList.remove('error');
            this.validatedUrl = url;
            this.urlFilenameGroup.style.display = 'block';
            this.uploadBtn.disabled = false;

            // Try to suggest a filename from the URL
            const urlPath = new URL(url).pathname;
            const suggestedFilename = urlPath.split('/').pop();
            if (suggestedFilename && suggestedFilename.includes('.')) {
                this.urlFilenameInput.value = suggestedFilename;
            }

            this.showToast('URL validated successfully!', 'success');

        } catch (error) {
            // For no-cors requests, we might get here even for valid URLs
            // So we'll be more lenient and just check the URL format
            if (this.isValidUrlFormat(url)) {
                this.urlInput.classList.add('valid');
                this.urlInput.classList.remove('error');
                this.validatedUrl = url;
                this.urlFilenameGroup.style.display = 'block';
                this.uploadBtn.disabled = false;

                this.showToast('URL format is valid. Proceeding with download...', 'success');
            } else {
                this.urlInput.classList.add('error');
                this.urlInput.classList.remove('valid');
                this.showToast('Unable to validate URL. Please check the link.', 'error');
            }
        } finally {
            this.urlValidateBtn.disabled = false;
            this.urlValidateBtn.innerHTML = '<i class="fas fa-check"></i> Validate';
        }
    }

    isStreamingPlatform(url) {
        const streamingDomains = [
            'youtube.com', 'youtu.be', 'vimeo.com', 'twitch.tv',
            'facebook.com', 'instagram.com', 'tiktok.com', 'dailymotion.com'
        ];

        try {
            const urlObj = new URL(url);
            const domain = urlObj.hostname.toLowerCase().replace('www.', '');
            return streamingDomains.some(streamingDomain =>
                domain === streamingDomain || domain.endsWith('.' + streamingDomain)
            );
        } catch {
            return false;
        }
    }

    resetUrlForm() {
        this.urlInput.value = '';
        this.urlFilenameInput.value = '';
        this.urlInput.classList.remove('valid', 'error');
        this.validatedUrl = null;
        this.urlFilenameGroup.style.display = 'none';
        this.urlValidateBtn.disabled = true;
    }

    // Transcript upload methods
    handleTranscriptFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Check file type
        const allowedTypes = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(file.type)) {
            this.showToast('Please select a TXT, PDF, or DOCX file', 'error');
            return;
        }

        // Read file content
        const reader = new FileReader();
        reader.onload = (e) => {
            if (file.type === 'text/plain') {
                this.transcriptText.value = e.target.result;
                this.handleTranscriptTextInput();
            } else {
                // For PDF/DOCX, we'll need to send to backend for processing
                this.transcriptContent = {
                    type: 'file',
                    file: file,
                    name: file.name
                };
                this.updateTranscriptUploadState();
            }
        };

        if (file.type === 'text/plain') {
            reader.readAsText(file);
        } else {
            reader.readAsArrayBuffer(file);
        }
    }

    handleTranscriptTextInput() {
        const text = this.transcriptText.value.trim();
        if (text.length > 0) {
            this.transcriptContent = {
                type: 'text',
                content: text
            };
            this.updateTranscriptUploadState();
        } else {
            this.transcriptContent = null;
            this.processTranscriptBtn.disabled = true;
        }
    }

    updateTranscriptUploadState() {
        const hasContent = this.transcriptContent !== null;
        this.processTranscriptBtn.disabled = !hasContent;

        if (hasContent && this.transcriptContent.type === 'file') {
            this.showToast(`File "${this.transcriptContent.name}" loaded successfully`, 'success');
        }
    }

    clearTranscript() {
        this.transcriptText.value = '';
        this.transcriptFileInput.value = '';
        this.transcriptContent = null;
        this.processTranscriptBtn.disabled = true;
    }

    resetTranscriptForm() {
        this.clearTranscript();
    }

    // Transcript drag and drop handlers
    handleTranscriptDragOver(event) {
        event.preventDefault();
        this.transcriptFileUploadArea.classList.add('dragover');
    }

    handleTranscriptDragLeave(event) {
        event.preventDefault();
        this.transcriptFileUploadArea.classList.remove('dragover');
    }

    handleTranscriptDrop(event) {
        event.preventDefault();
        this.transcriptFileUploadArea.classList.remove('dragover');

        const files = event.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            // Simulate file input change event
            this.handleTranscriptFileSelect({ target: { files: [file] } });
        }
    }

    async processTranscript() {
        if (!this.transcriptContent) {
            this.showToast('Please provide a transcript first', 'error');
            return;
        }

        try {
            this.showLoading('Processing transcript...');

            const formData = new FormData();

            if (this.transcriptContent.type === 'text') {
                // Send text content
                formData.append('transcript_text', this.transcriptContent.content);
                formData.append('upload_type', 'transcript_text');
            } else {
                // Send file
                formData.append('transcript_file', this.transcriptContent.file);
                formData.append('upload_type', 'transcript_file');
            }

            // Add processing options
            formData.append('language', this.languageSelect.value);
            formData.append('format', this.formatSelect.value);

            const response = await fetch(`${this.apiBaseUrl}/api/upload`, {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });

            const result = await response.json();

            if (response.ok) {
                this.currentJobId = result.job_id;
                this.showProcessingSection(result);
                this.startPolling();
            } else {
                throw new Error(result.message || 'Upload failed');
            }
        } catch (error) {
            this.showToast('Failed to process transcript: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // Upload and processing methods
    async startUpload() {
        if (this.uploadMethod === 'file') {
            return this.startFileUpload();
        } else if (this.uploadMethod === 'url') {
            return this.startUrlUpload();
        } else if (this.uploadMethod === 'transcript') {
            return this.processTranscript();
        }
    }

    async startFileUpload() {
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
                body: formData,
                credentials: 'include'
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

    async startUrlUpload() {
        if (!this.validatedUrl) {
            this.showToast('Please validate a URL first.', 'error');
            return;
        }

        this.showLoading('Downloading from URL...');

        try {
            const requestData = {
                url: this.validatedUrl,
                filename: this.urlFilenameInput.value.trim() || undefined,
                language: this.languageSelect.value,
                format: this.formatSelect.value
            };

            const response = await fetch(`${this.apiBaseUrl}/api/upload-url`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(requestData)
            });

            const result = await response.json();

            if (result.success) {
                this.currentJobId = result.data.job_id;
                this.showProcessingSection(result.data);
                this.startPolling();
            } else {
                throw new Error(result.message || 'URL upload failed');
            }
        } catch (error) {
            this.showError('URL upload failed: ' + error.message);
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
                const response = await fetch(`${this.apiBaseUrl}/api/status/${this.currentJobId}`, {
                    credentials: 'include'
                });
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

    async downloadFile(format = 'primary') {
        if (!this.currentJobId) {
            this.showToast('No job ID available for download', 'error');
            return;
        }

        try {
            const formatText = format === 'primary' ? 'DOCX' : format.toUpperCase();
            this.showLoading(`Preparing ${formatText} download...`);

            // For now, all formats use the same endpoint since backend prioritizes formats
            // In the future, we could add format-specific endpoints
            const response = await fetch(`${this.apiBaseUrl}/api/download/${this.currentJobId}`, {
                credentials: 'include'
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;

                // Get filename from Content-Disposition header or use default
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = `meeting-minutes-${this.currentJobId}.json`;
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                    if (filenameMatch) {
                        filename = filenameMatch[1];
                    }
                }

                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                this.showToast(`Meeting minutes downloaded successfully!`, 'success');
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

    async viewPreview() {
        if (!this.currentJobId) {
            this.showToast('No job ID available for preview', 'error');
            return;
        }

        try {
            this.showLoading('Loading preview...');

            // Fetch the HTML preview from the server
            const response = await fetch(`${this.apiBaseUrl}/api/preview/${this.currentJobId}`, {
                credentials: 'include'
            });

            if (response.ok) {
                const blob = await response.blob();

                // Check if it's an HTML file
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('text/html')) {
                    // Create a blob URL and open in new window
                    const url = window.URL.createObjectURL(blob);
                    const previewWindow = window.open(url, '_blank', 'width=1000,height=800,scrollbars=yes,resizable=yes');

                    if (previewWindow) {
                        // Clean up the blob URL after a delay
                        setTimeout(() => {
                            window.URL.revokeObjectURL(url);
                        }, 1000);
                        this.showToast('Preview opened in new window', 'success');
                    } else {
                        this.showToast('Please allow popups to view preview', 'warning');
                    }
                } else {
                    // If not HTML, show a modal with preview info
                    this.showPreviewModal();
                }
            } else {
                const result = await response.json();
                throw new Error(result.message || 'Preview failed');
            }
        } catch (error) {
            this.showToast('Preview failed: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    showPreviewModal() {
        // Create a simple preview modal for non-HTML files
        const modal = document.createElement('div');
        modal.className = 'preview-modal';
        modal.innerHTML = `
            <div class="preview-modal-content">
                <div class="preview-modal-header">
                    <h3>Meeting Minutes Preview</h3>
                    <button class="preview-modal-close">&times;</button>
                </div>
                <div class="preview-modal-body">
                    <p>📄 Your meeting minutes have been generated successfully!</p>
                    <p>The document contains:</p>
                    <ul>
                        <li>✅ Meeting information and attendees</li>
                        <li>✅ Agenda items and discussions</li>
                        <li>✅ Motions and voting results</li>
                        <li>✅ Action items and key decisions</li>
                    </ul>
                    <p>Download the document to view the full content.</p>
                </div>
                <div class="preview-modal-footer">
                    <button class="download-btn primary" onclick="this.closest('.preview-modal').remove(); app.downloadFile('primary')">
                        Download DOCX
                    </button>
                    <button class="download-btn secondary" onclick="this.closest('.preview-modal').remove()">
                        Close
                    </button>
                </div>
            </div>
        `;

        // Add click handler for close button
        modal.querySelector('.preview-modal-close').addEventListener('click', () => {
            modal.remove();
        });

        // Add click handler for modal background
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        document.body.appendChild(modal);
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
        this.resetUrlForm();
        this.resetTranscriptForm();
        this.showSection('upload');

        // Reset all steps - add null checks to prevent errors on different pages
        Object.values(this.steps).forEach(step => {
            if (step && step.classList) {
                step.classList.remove('active', 'completed', 'error');
                const statusIcon = step.querySelector('.step-status i');
                if (statusIcon) {
                    statusIcon.className = 'fas fa-clock';
                }
            }
        });

        // Reset progress
        this.updateProgress(0, 'Ready to upload');
    }

    // UI utility methods
    showSection(sectionName) {
        Object.values(this.sections).forEach(section => {
            // Add null check to prevent errors when section doesn't exist
            if (section && section.classList) {
                section.classList.remove('active');
            }
        });

        if (this.sections[sectionName] && this.sections[sectionName].classList) {
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

    async showReviewModal() {
        if (!this.currentJobId) {
            this.showToast('No job ID available for review', 'error');
            return;
        }

        try {
            this.showLoading('Loading content for review...');

            // For now, create a simple review modal with mock data
            // In a real implementation, this would fetch the actual AI results
            const mockResults = {
                attendees: ['John Smith', 'Jane Doe', 'Bob Johnson'],
                agenda_items: ['Budget Review', 'Project Updates', 'New Initiatives'],
                motions: ['Approve Q4 Budget', 'Hire New Developer'],
                action_items: ['John to prepare budget report by Friday', 'Jane to schedule follow-up meeting']
            };

            this.createReviewModal(mockResults);
        } catch (error) {
            this.showToast('Failed to load content for review: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    createReviewModal(aiResults) {
        // Create the review modal
        const modal = document.createElement('div');
        modal.className = 'review-modal';
        modal.innerHTML = `
            <div class="review-modal-content">
                <div class="review-modal-header">
                    <h3><i class="fas fa-edit"></i> Review & Edit AI Results</h3>
                    <button class="review-modal-close">&times;</button>
                </div>
                <div class="review-modal-body">
                    <div class="review-section">
                        <h4><i class="fas fa-users"></i> Meeting Attendees</h4>
                        <div class="editable-list">
                            ${(aiResults.attendees || []).map((attendee, index) => `
                                <div class="editable-item">
                                    <input type="text" value="${attendee}" class="edit-input">
                                    <button class="remove-item" data-index="${index}">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                        <button class="add-item-btn" data-type="attendee">
                            <i class="fas fa-plus"></i> Add Attendee
                        </button>
                    </div>

                    <div class="review-section">
                        <h4><i class="fas fa-list"></i> Agenda Items</h4>
                        <div class="editable-list">
                            ${(aiResults.agenda_items || []).map((item, index) => `
                                <div class="editable-item">
                                    <input type="text" value="${item}" class="edit-input">
                                    <button class="remove-item" data-index="${index}">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                        <button class="add-item-btn" data-type="agenda">
                            <i class="fas fa-plus"></i> Add Agenda Item
                        </button>
                    </div>

                    <div class="review-section">
                        <h4><i class="fas fa-gavel"></i> Motions</h4>
                        <div class="editable-list">
                            ${(aiResults.motions || []).map((motion, index) => `
                                <div class="editable-item">
                                    <input type="text" value="${motion}" class="edit-input">
                                    <button class="remove-item" data-index="${index}">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                        <button class="add-item-btn" data-type="motion">
                            <i class="fas fa-plus"></i> Add Motion
                        </button>
                    </div>

                    <div class="review-section">
                        <h4><i class="fas fa-tasks"></i> Action Items</h4>
                        <div class="editable-list">
                            ${(aiResults.action_items || []).map((action, index) => `
                                <div class="editable-item">
                                    <input type="text" value="${action}" class="edit-input">
                                    <button class="remove-item" data-index="${index}">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                        <button class="add-item-btn" data-type="action">
                            <i class="fas fa-plus"></i> Add Action Item
                        </button>
                    </div>
                </div>
                <div class="review-modal-footer">
                    <button class="btn secondary" onclick="this.closest('.review-modal').remove()">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                    <button class="btn primary" id="save-changes-btn">
                        <i class="fas fa-save"></i> Save Changes & Regenerate
                    </button>
                </div>
            </div>
        `;

        // Add event listeners
        this.setupReviewModalEvents(modal);

        document.body.appendChild(modal);
    }

    setupReviewModalEvents(modal) {
        // Close button
        modal.querySelector('.review-modal-close').addEventListener('click', () => {
            modal.remove();
        });

        // Click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        // Add item buttons
        modal.querySelectorAll('.add-item-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const type = e.target.closest('.add-item-btn').dataset.type;
                const list = e.target.closest('.review-section').querySelector('.editable-list');
                const newItem = document.createElement('div');
                newItem.className = 'editable-item';
                newItem.innerHTML = `
                    <input type="text" value="New ${type}" class="edit-input">
                    <button class="remove-item">
                        <i class="fas fa-trash"></i>
                    </button>
                `;
                list.appendChild(newItem);

                // Focus the new input
                newItem.querySelector('.edit-input').focus();
                newItem.querySelector('.edit-input').select();
            });
        });

        // Remove item buttons (using event delegation)
        modal.addEventListener('click', (e) => {
            if (e.target.closest('.remove-item')) {
                e.target.closest('.editable-item').remove();
            }
        });

        // Save changes button
        modal.querySelector('#save-changes-btn').addEventListener('click', () => {
            this.saveReviewChanges(modal);
        });
    }

    saveReviewChanges(modal) {
        this.showToast('Changes saved! Documents will be regenerated with your edits.', 'success');
        modal.remove();

        // In a real implementation, this would:
        // 1. Collect all the edited data from the form
        // 2. Send it back to the server to regenerate documents
        // 3. Update the download links with new files
    }

    initializeTheme() {
        // Check for saved theme preference or default to light mode
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

        // Update theme toggle icon
        const icon = this.themeToggle.querySelector('i');
        if (theme === 'dark') {
            icon.className = 'fas fa-sun';
            this.themeToggle.title = 'Switch to light mode';
        } else {
            icon.className = 'fas fa-moon';
            this.themeToggle.title = 'Switch to dark mode';
        }

        // Add smooth transition effect
        document.body.style.transition = 'background 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }

    initializeLogo() {
        const logoImage = document.querySelector('.logo-image');
        if (logoImage) {
            // Handle logo loading error
            logoImage.addEventListener('error', () => {
                console.warn('Logo image failed to load, using fallback');
                logoImage.style.display = 'none';

                // Add fallback icon to the title
                const title = logoImage.nextElementSibling;
                if (title && !title.textContent.includes('🧠')) {
                    title.textContent = '🧠 ' + title.textContent;
                }
            });

            // Handle successful logo load
            logoImage.addEventListener('load', () => {
                console.log('Logo loaded successfully');
                logoImage.style.opacity = '0';
                logoImage.style.transform = 'scale(0.8)';

                // Animate in
                setTimeout(() => {
                    logoImage.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                    logoImage.style.opacity = '1';
                    logoImage.style.transform = 'scale(1)';
                }, 100);
            });
        }
    }

    async checkAuthentication() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/auth/check`, {
                credentials: 'include'
            });

            if (!response.ok) {
                // User not authenticated, redirect to auth page
                window.location.href = '/frontend/auth.html';
                return;
            }

            const result = await response.json();
            if (!result.success) {
                // User not authenticated, redirect to auth page
                window.location.href = '/frontend/auth.html';
                return;
            }

            // User is authenticated, store user info
            this.currentUser = result.data.user;
            this.updateUIForAuthenticatedUser();

        } catch (error) {
            console.log('Authentication check failed, redirecting to login');
            // Redirect to auth page on error
            window.location.href = '/frontend/auth.html';
        }
    }

    updateUIForAuthenticatedUser() {
        // Add user info to header if authenticated
        if (this.currentUser) {
            const headerControls = document.querySelector('.header-controls');
            if (headerControls && !document.querySelector('.user-menu')) {
                const userMenu = document.createElement('div');
                userMenu.className = 'user-menu';
                userMenu.innerHTML = `
                    <button class="user-menu-toggle" title="User menu">
                        <i class="fas fa-user-circle"></i>
                        <span>${this.currentUser.first_name}</span>
                    </button>
                    <div class="user-dropdown">
                        <div class="user-info">
                            <strong>${this.currentUser.full_name}</strong>
                            <small>${this.currentUser.email}</small>
                        </div>
                        <hr>
                        <a href="/frontend/dashboard.html" class="dropdown-item">
                            <i class="fas fa-tachometer-alt"></i> Dashboard
                        </a>
                        <a href="/frontend/templates.html" class="dropdown-item">
                            <i class="fas fa-file-alt"></i> Templates
                        </a>
                        <a href="/frontend/calendar.html" class="dropdown-item">
                            <i class="fas fa-calendar-alt"></i> Calendar
                        </a>
                        <a href="/frontend/batch.html" class="dropdown-item">
                            <i class="fas fa-layer-group"></i> Batch Processing
                        </a>
                        <a href="/frontend/profile.html" class="dropdown-item">
                            <i class="fas fa-user-cog"></i> Profile & Settings
                        </a>
                        <a href="#" class="dropdown-item" id="user-meetings">
                            <i class="fas fa-history"></i> Meeting History
                        </a>
                        <a href="#" class="dropdown-item" id="user-settings">
                            <i class="fas fa-cog"></i> Settings
                        </a>
                        <hr>
                        <a href="#" class="dropdown-item" id="user-logout">
                            <i class="fas fa-sign-out-alt"></i> Logout
                        </a>
                    </div>
                `;

                // Insert before theme toggle
                headerControls.insertBefore(userMenu, this.themeToggle);

                // Add event listeners
                this.setupUserMenu(userMenu);
            }
        }
    }

    setupUserMenu(userMenu) {
        const toggle = userMenu.querySelector('.user-menu-toggle');
        const dropdown = userMenu.querySelector('.user-dropdown');

        toggle.addEventListener('click', () => {
            dropdown.classList.toggle('show');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!userMenu.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });

        // Logout functionality
        userMenu.querySelector('#user-logout').addEventListener('click', async (e) => {
            e.preventDefault();
            await this.logout();
        });
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
            // Clear local storage and redirect
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/frontend/auth.html';
        }
    }

    async loadUserPreferences() {
        try {
            // First check if user is authenticated
            const authResponse = await fetch(`${this.apiBaseUrl}/api/auth/check`, {
                credentials: 'include'
            });

            if (authResponse.ok) {
                const authResult = await authResponse.json();
                if (authResult.success) {
                    // User is authenticated, show user menu and load preferences
                    this.showUserInfo(authResult.data.user);

                    // Load user preferences
                    const prefResponse = await fetch(`${this.apiBaseUrl}/api/auth/preferences`, {
                        credentials: 'include'
                    });

                    if (prefResponse.ok) {
                        const prefResult = await prefResponse.json();
                        if (prefResult.success) {
                            this.applyUserPreferences(prefResult.data.preferences);
                        } else {
                            this.applyUserPreferences({});
                        }
                    } else {
                        this.applyUserPreferences({});
                    }
                } else {
                    // User not authenticated, hide user menu
                    this.hideUserMenu();
                    this.applyUserPreferences({});
                }
            } else {
                // User not authenticated, hide user menu
                this.hideUserMenu();
                this.applyUserPreferences({});
            }
        } catch (error) {
            console.log('Could not load user preferences, using defaults:', error);
            this.hideUserMenu();
            this.applyUserPreferences({});
        }
    }

    showUserInfo(user) {
        if (this.userMenu) {
            this.userMenu.style.display = 'block';
            if (this.userName) this.userName.textContent = user.first_name || user.username;
            if (this.userFullName) this.userFullName.textContent = user.full_name || `${user.first_name} ${user.last_name}`;
            if (this.userEmail) this.userEmail.textContent = user.email;
        }
    }

    hideUserMenu() {
        if (this.userMenu) {
            this.userMenu.style.display = 'none';
        }
    }

    applyUserPreferences(preferences) {
        // Apply default language preference
        if (preferences.meeting_default_language && this.languageSelect) {
            this.languageSelect.value = preferences.meeting_default_language;
        }

        // Apply default template preference
        if (preferences.meeting_default_template && this.formatSelect) {
            // Map template names to format select values
            const templateMapping = {
                'professional': 'corporate',
                'formal': 'roberts_rules',
                'casual': 'informal',
                'academic': 'roberts_rules'
            };

            const formatValue = templateMapping[preferences.meeting_default_template] || 'roberts_rules';
            this.formatSelect.value = formatValue;
        }

        // Apply theme preference if available
        if (preferences.user_theme) {
            this.applyTheme(preferences.user_theme);
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
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MinuteMateApp();
});
