/**
 * MinuteMate Templates JavaScript
 * Handles template management, creation, and customization
 */

class TemplatesApp {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.currentUser = null;
        this.templates = [];
        this.availableSections = {};
        this.editingTemplate = null;
        
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
        
        // Templates elements
        this.templatesGrid = document.getElementById('templates-grid');
        this.categoryFilter = document.getElementById('category-filter');
        this.includePublic = document.getElementById('include-public');
        this.createTemplateBtn = document.getElementById('create-template-btn');
        this.createDefaultsBtn = document.getElementById('create-defaults-btn');
        
        // Modal elements
        this.templateModal = document.getElementById('template-modal');
        this.modalTitle = document.getElementById('modal-title');
        this.templateForm = document.getElementById('template-form');
        this.sectionsGrid = document.getElementById('sections-grid');
        this.saveTemplateBtn = document.getElementById('save-template');
        this.cancelTemplateBtn = document.getElementById('cancel-template');
        
        // Confirmation modal
        this.confirmationModal = document.getElementById('confirmation-modal');
        this.confirmationMessage = document.getElementById('confirmation-message');
        this.confirmActionBtn = document.getElementById('confirm-action');
        this.cancelConfirmationBtn = document.getElementById('cancel-confirmation');
        
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

        // Template actions
        this.createTemplateBtn.addEventListener('click', () => this.openTemplateModal());
        this.createDefaultsBtn.addEventListener('click', () => this.createDefaultTemplates());
        
        // Filters
        this.categoryFilter.addEventListener('change', () => this.loadTemplates());
        this.includePublic.addEventListener('change', () => this.loadTemplates());
        
        // Modal actions
        this.templateForm.addEventListener('submit', this.saveTemplate.bind(this));
        this.cancelTemplateBtn.addEventListener('click', () => this.closeTemplateModal());
        this.templateModal.querySelector('.template-modal-close').addEventListener('click', () => this.closeTemplateModal());
        
        // Confirmation modal
        this.cancelConfirmationBtn.addEventListener('click', () => this.closeConfirmationModal());
        
        // Close modals when clicking outside
        this.templateModal.addEventListener('click', (e) => {
            if (e.target === this.templateModal) {
                this.closeTemplateModal();
            }
        });
        
        this.confirmationModal.addEventListener('click', (e) => {
            if (e.target === this.confirmationModal) {
                this.closeConfirmationModal();
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
            this.loadAvailableSections();
            this.loadTemplates();
            
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

    async loadAvailableSections() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/templates/sections`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.availableSections = result.data.sections;
                }
            }
        } catch (error) {
            console.error('Failed to load available sections:', error);
        }
    }

    async loadTemplates() {
        try {
            this.showLoading('Loading templates...');
            
            const category = this.categoryFilter.value;
            const includePublic = this.includePublic.checked;
            
            const params = new URLSearchParams({
                category: category,
                include_public: includePublic
            });
            
            const response = await fetch(`${this.apiBaseUrl}/api/templates/?${params}`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.templates = result.data.templates;
                    this.renderTemplates();
                } else {
                    throw new Error(result.message);
                }
            } else {
                throw new Error('Failed to load templates');
            }
        } catch (error) {
            console.error('Templates load error:', error);
            this.showToast('Failed to load templates', 'error');
            this.templatesGrid.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Failed to load templates</h3>
                    <p>Please try refreshing the page</p>
                </div>
            `;
        } finally {
            this.hideLoading();
        }
    }

    renderTemplates() {
        if (!this.templates || this.templates.length === 0) {
            this.templatesGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-alt"></i>
                    <h3>No templates found</h3>
                    <p>Create your first template or add some default templates to get started!</p>
                    <button class="btn primary" onclick="templatesApp.createDefaultTemplates()">
                        <i class="fas fa-magic"></i> Create Default Templates
                    </button>
                </div>
            `;
            return;
        }

        const templatesHtml = this.templates.map(template => `
            <div class="template-card" data-template-id="${template.id}">
                <div class="template-header">
                    <div class="template-info">
                        <h3>${template.name}</h3>
                        <span class="template-category">${this.getCategoryLabel(template.category)}</span>
                    </div>
                    <div class="template-actions">
                        <button class="btn-icon" onclick="templatesApp.editTemplate('${template.id}')" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon" onclick="templatesApp.duplicateTemplate('${template.id}')" title="Duplicate">
                            <i class="fas fa-copy"></i>
                        </button>
                        ${template.user_id === this.currentUser.id ? `
                            <button class="btn-icon danger" onclick="templatesApp.deleteTemplate('${template.id}')" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </div>
                
                <div class="template-body">
                    ${template.description ? `<p class="template-description">${template.description}</p>` : ''}
                    
                    <div class="template-meta">
                        <div class="template-sections">
                            <strong>Sections:</strong>
                            <span>${this.getEnabledSections(template.sections).join(', ')}</span>
                        </div>
                        <div class="template-style">
                            <strong>Style:</strong>
                            <span>${template.formatting_options?.style || 'Professional'}</span>
                        </div>
                    </div>
                    
                    <div class="template-footer">
                        <div class="template-badges">
                            ${template.is_public ? '<span class="badge public">Public</span>' : '<span class="badge private">Private</span>'}
                            ${template.user_id !== this.currentUser.id ? '<span class="badge shared">Shared</span>' : ''}
                        </div>
                        <div class="template-stats">
                            <span class="usage-count">
                                <i class="fas fa-chart-bar"></i>
                                Used ${template.usage_count || 0} times
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        this.templatesGrid.innerHTML = templatesHtml;
    }

    getCategoryLabel(category) {
        const categories = {
            'board': 'Board Meeting',
            'governance': 'Governance & Parliamentary',
            'team': 'Team Meeting',
            'project': 'Project Meeting',
            'client': 'Client Meeting',
            'general': 'General',
            'training': 'Training',
            'interview': 'Interview',
            'sales': 'Sales'
        };
        return categories[category] || 'General';
    }

    getEnabledSections(sections) {
        if (!sections) return ['Header'];
        
        const enabled = [];
        for (const [key, config] of Object.entries(sections)) {
            if (config.enabled) {
                const sectionName = this.availableSections[key]?.name || key.charAt(0).toUpperCase() + key.slice(1);
                enabled.push(sectionName);
            }
        }
        return enabled.length > 0 ? enabled : ['Header'];
    }

    openTemplateModal(template = null) {
        this.editingTemplate = template;
        
        if (template) {
            this.modalTitle.innerHTML = '<i class="fas fa-edit"></i> Edit Template';
            this.populateForm(template);
        } else {
            this.modalTitle.innerHTML = '<i class="fas fa-plus"></i> Create Template';
            this.templateForm.reset();
        }
        
        this.renderSectionsGrid();
        this.templateModal.classList.add('show');
    }

    closeTemplateModal() {
        this.templateModal.classList.remove('show');
        this.editingTemplate = null;
        this.templateForm.reset();
    }

    renderSectionsGrid() {
        const sectionsHtml = Object.entries(this.availableSections).map(([key, section]) => `
            <div class="section-config">
                <div class="section-header">
                    <label class="section-toggle">
                        <input type="checkbox" name="section_${key}" ${this.editingTemplate?.sections?.[key]?.enabled ? 'checked' : ''}>
                        <span class="section-name">${section.name}</span>
                    </label>
                </div>
                <p class="section-description">${section.description}</p>
                <div class="section-options" id="options_${key}">
                    ${section.options.map(option => `
                        <label class="option-label">
                            <input type="checkbox" name="${key}_${option}" 
                                   ${this.editingTemplate?.sections?.[key]?.[option] ? 'checked' : ''}>
                            <span>${option.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
        `).join('');
        
        this.sectionsGrid.innerHTML = sectionsHtml;
    }

    populateForm(template) {
        document.getElementById('template-name').value = template.name || '';
        document.getElementById('template-category').value = template.category || 'general';
        document.getElementById('template-description').value = template.description || '';
        document.getElementById('template-public').checked = template.is_public || false;
        
        // Formatting options
        const formatting = template.formatting_options || {};
        document.getElementById('template-style').value = formatting.style || 'professional';
        document.getElementById('template-font').value = formatting.font_family || 'Arial';
        document.getElementById('template-font-size').value = formatting.font_size || 11;
        document.getElementById('template-line-spacing').value = formatting.line_spacing || 1.2;
    }

    async saveTemplate(e) {
        e.preventDefault();
        
        try {
            this.showLoading('Saving template...');
            
            const formData = new FormData(this.templateForm);
            const templateData = {
                name: formData.get('name'),
                category: formData.get('category'),
                description: formData.get('description'),
                is_public: formData.get('is_public') === 'on',
                sections: this.collectSectionsData(),
                formatting_options: {
                    style: formData.get('style'),
                    font_family: formData.get('font_family'),
                    font_size: parseInt(formData.get('font_size')),
                    line_spacing: parseFloat(formData.get('line_spacing'))
                }
            };
            
            const url = this.editingTemplate 
                ? `${this.apiBaseUrl}/api/templates/${this.editingTemplate.id}`
                : `${this.apiBaseUrl}/api/templates/`;
            
            const method = this.editingTemplate ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(templateData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast(
                    this.editingTemplate ? 'Template updated successfully' : 'Template created successfully',
                    'success'
                );
                this.closeTemplateModal();
                this.loadTemplates();
            } else {
                throw new Error(result.message);
            }
            
        } catch (error) {
            console.error('Save template error:', error);
            this.showToast('Failed to save template', 'error');
        } finally {
            this.hideLoading();
        }
    }

    collectSectionsData() {
        const sections = {};
        
        Object.keys(this.availableSections).forEach(sectionKey => {
            const checkbox = document.querySelector(`input[name="section_${sectionKey}"]`);
            const enabled = checkbox ? checkbox.checked : false;
            
            sections[sectionKey] = { enabled };
            
            // Collect section options
            if (enabled) {
                this.availableSections[sectionKey].options.forEach(option => {
                    const optionCheckbox = document.querySelector(`input[name="${sectionKey}_${option}"]`);
                    if (optionCheckbox) {
                        sections[sectionKey][option] = optionCheckbox.checked;
                    }
                });
            }
        });
        
        return sections;
    }

    async editTemplate(templateId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/templates/${templateId}`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.openTemplateModal(result.data.template);
                } else {
                    throw new Error(result.message);
                }
            } else {
                throw new Error('Failed to load template');
            }
        } catch (error) {
            console.error('Edit template error:', error);
            this.showToast('Failed to load template for editing', 'error');
        }
    }

    async duplicateTemplate(templateId) {
        try {
            this.showLoading('Duplicating template...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/templates/${templateId}/duplicate`, {
                method: 'POST',
                credentials: 'include'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Template duplicated successfully', 'success');
                this.loadTemplates();
            } else {
                throw new Error(result.message);
            }
            
        } catch (error) {
            console.error('Duplicate template error:', error);
            this.showToast('Failed to duplicate template', 'error');
        } finally {
            this.hideLoading();
        }
    }

    deleteTemplate(templateId) {
        this.confirmationMessage.textContent = 'Are you sure you want to delete this template? This action cannot be undone.';
        this.confirmActionBtn.onclick = () => this.confirmDeleteTemplate(templateId);
        this.confirmationModal.classList.add('show');
    }

    async confirmDeleteTemplate(templateId) {
        try {
            this.closeConfirmationModal();
            this.showLoading('Deleting template...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/templates/${templateId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Template deleted successfully', 'success');
                this.loadTemplates();
            } else {
                throw new Error(result.message);
            }
            
        } catch (error) {
            console.error('Delete template error:', error);
            this.showToast('Failed to delete template', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async createDefaultTemplates() {
        try {
            this.showLoading('Creating default templates...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/templates/defaults`, {
                method: 'POST',
                credentials: 'include'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast(`Created ${result.data.templates.length} default templates`, 'success');
                this.loadTemplates();
            } else {
                throw new Error(result.message);
            }
            
        } catch (error) {
            console.error('Create defaults error:', error);
            this.showToast('Failed to create default templates', 'error');
        } finally {
            this.hideLoading();
        }
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

// Initialize the templates app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.templatesApp = new TemplatesApp();
});
