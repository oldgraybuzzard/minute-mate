/**
 * MinuteMate Authentication JavaScript
 * Handles user login, registration, and authentication flows
 */

class AuthApp {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.currentForm = 'login-form';
        
        this.initializeElements();
        this.setupEventListeners();
        this.initializeTheme();
        this.checkAuthStatus();
    }

    initializeElements() {
        // Forms
        this.loginForm = document.getElementById('login-form-element');
        this.registerForm = document.getElementById('register-form-element');
        
        // Form containers
        this.loginContainer = document.getElementById('login-form');
        this.registerContainer = document.getElementById('register-form');
        
        // UI elements
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.toast = document.getElementById('toast');
        this.themeToggle = document.getElementById('theme-toggle');
        
        // Password strength
        this.passwordStrength = document.getElementById('password-strength');
    }

    setupEventListeners() {
        // Form submissions
        this.loginForm.addEventListener('submit', this.handleLogin.bind(this));
        this.registerForm.addEventListener('submit', this.handleRegister.bind(this));
        
        // Form switching
        document.querySelectorAll('.switch-form').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetForm = e.target.dataset.target;
                this.switchForm(targetForm);
            });
        });
        
        // Password toggles
        document.querySelectorAll('.password-toggle').forEach(toggle => {
            toggle.addEventListener('click', this.togglePassword.bind(this));
        });
        
        // Password strength checker
        const registerPassword = document.getElementById('register-password');
        registerPassword.addEventListener('input', this.checkPasswordStrength.bind(this));
        
        // Theme toggle
        this.themeToggle.addEventListener('click', this.toggleTheme.bind(this));
        
        // Toast close
        this.toast.querySelector('.toast-close').addEventListener('click', () => {
            this.toast.classList.remove('show');
        });
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const formData = new FormData(this.loginForm);
        const loginData = {
            login: formData.get('login'),
            password: formData.get('password'),
            remember: formData.get('remember') === 'on'
        };

        try {
            this.showLoading('Signing in...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(loginData)
            });

            const result = await response.json();

            if (result.success) {
                // Store tokens
                if (result.data.access_token) {
                    localStorage.setItem('access_token', result.data.access_token);
                }
                if (result.data.refresh_token) {
                    localStorage.setItem('refresh_token', result.data.refresh_token);
                }
                
                this.showToast('Login successful! Redirecting...', 'success');
                
                // Redirect to main app
                setTimeout(() => {
                    window.location.href = '/frontend/';
                }, 1500);
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            this.showToast('Login failed. Please try again.', 'error');
            console.error('Login error:', error);
        } finally {
            this.hideLoading();
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        
        const formData = new FormData(this.registerForm);
        const password = formData.get('password');
        const confirmPassword = formData.get('confirm_password');
        
        // Validate passwords match
        if (password !== confirmPassword) {
            this.showToast('Passwords do not match', 'error');
            return;
        }
        
        const registerData = {
            email: formData.get('email'),
            username: formData.get('username'),
            password: password,
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name')
        };

        try {
            this.showLoading('Creating account...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(registerData)
            });

            const result = await response.json();

            if (result.success) {
                this.showToast('Account created successfully! Please sign in.', 'success');
                this.switchForm('login-form');
                
                // Pre-fill login form
                document.getElementById('login-identifier').value = registerData.email;
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            this.showToast('Registration failed. Please try again.', 'error');
            console.error('Registration error:', error);
        } finally {
            this.hideLoading();
        }
    }

    switchForm(targetForm) {
        // Hide current form
        document.querySelectorAll('.auth-form').forEach(form => {
            form.classList.remove('active');
        });
        
        // Show target form
        document.getElementById(targetForm).classList.add('active');
        this.currentForm = targetForm;
        
        // Clear forms
        this.loginForm.reset();
        this.registerForm.reset();
        this.passwordStrength.style.display = 'none';
    }

    togglePassword(e) {
        const targetId = e.target.closest('.password-toggle').dataset.target;
        const passwordInput = document.getElementById(targetId);
        const icon = e.target.closest('.password-toggle').querySelector('i');
        
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            passwordInput.type = 'password';
            icon.className = 'fas fa-eye';
        }
    }

    checkPasswordStrength(e) {
        const password = e.target.value;
        const strengthContainer = this.passwordStrength;
        const strengthFill = strengthContainer.querySelector('.strength-fill');
        const strengthText = strengthContainer.querySelector('.strength-text');
        
        if (password.length === 0) {
            strengthContainer.style.display = 'none';
            return;
        }
        
        strengthContainer.style.display = 'block';
        
        let score = 0;
        let feedback = [];
        
        // Length check
        if (password.length >= 8) score += 1;
        else feedback.push('at least 8 characters');
        
        // Uppercase check
        if (/[A-Z]/.test(password)) score += 1;
        else feedback.push('uppercase letter');
        
        // Lowercase check
        if (/[a-z]/.test(password)) score += 1;
        else feedback.push('lowercase letter');
        
        // Number check
        if (/\d/.test(password)) score += 1;
        else feedback.push('number');
        
        // Special character check
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score += 1;
        else feedback.push('special character');
        
        // Update UI
        const percentage = (score / 5) * 100;
        strengthFill.style.width = `${percentage}%`;
        
        if (score <= 2) {
            strengthFill.className = 'strength-fill weak';
            strengthText.textContent = `Weak - Add ${feedback.slice(0, 2).join(', ')}`;
        } else if (score <= 3) {
            strengthFill.className = 'strength-fill medium';
            strengthText.textContent = `Medium - Add ${feedback.slice(0, 1).join(', ')}`;
        } else if (score <= 4) {
            strengthFill.className = 'strength-fill strong';
            strengthText.textContent = 'Strong';
        } else {
            strengthFill.className = 'strength-fill very-strong';
            strengthText.textContent = 'Very Strong';
        }
    }

    async checkAuthStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/auth/check`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // User is already logged in, redirect to main app
                    window.location.href = '/frontend/';
                }
            }
        } catch (error) {
            // User not logged in, stay on auth page
            console.log('User not authenticated');
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

// Initialize the auth app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AuthApp();
});
