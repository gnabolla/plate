// Authentication utilities for JWT token management

const AUTH_TOKEN_KEY = 'auth_token';
const USER_DATA_KEY = 'user_data';

// Base URL for API calls
const API_BASE_URL = '/plate';

// Authentication class to handle all auth-related operations
class AuthManager {
    constructor() {
        this.token = localStorage.getItem(AUTH_TOKEN_KEY);
        this.userData = this.getUserData();
    }

    // Store token and user data
    setAuthData(token, userData) {
        this.token = token;
        this.userData = userData;
        localStorage.setItem(AUTH_TOKEN_KEY, token);
        localStorage.setItem(USER_DATA_KEY, JSON.stringify(userData));
    }

    // Get stored user data
    getUserData() {
        const data = localStorage.getItem(USER_DATA_KEY);
        return data ? JSON.parse(data) : null;
    }

    // Check if user is authenticated
    isAuthenticated() {
        return !!this.token && !!this.userData;
    }

    // Get user role
    getUserRole() {
        return this.userData?.role || null;
    }

    // Clear auth data (logout)
    clearAuth() {
        this.token = null;
        this.userData = null;
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(USER_DATA_KEY);
    }

    // Get auth headers for API requests
    getAuthHeaders() {
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }

    // Login method
    async login(username, password) {
        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);
            formData.append('grant_type', 'password');

            const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();
            
            // Get user info
            const userResponse = await fetch(`${API_BASE_URL}/api/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${data.access_token}`
                }
            });

            if (!userResponse.ok) {
                throw new Error('Failed to get user information');
            }

            const userData = await userResponse.json();
            
            // Store auth data
            this.setAuthData(data.access_token, userData);
            
            return { success: true, userData };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Logout method
    async logout() {
        try {
            if (this.token) {
                await fetch(`${API_BASE_URL}/api/auth/logout`, {
                    method: 'POST',
                    headers: this.getAuthHeaders()
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.clearAuth();
            window.location.href = '/plate/login';
        }
    }

    // Check token validity
    async checkAuth() {
        if (!this.token) return false;

        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                this.clearAuth();
                return false;
            }

            const userData = await response.json();
            this.userData = userData;
            localStorage.setItem(USER_DATA_KEY, JSON.stringify(userData));
            return true;
        } catch (error) {
            this.clearAuth();
            return false;
        }
    }

    // Get redirect URL based on role
    getRedirectUrl() {
        const role = this.getUserRole();
        switch (role) {
            case 'super_admin':
                return '/plate/admin/dashboard';
            case 'officer':
                return '/plate/officer/dashboard';
            case 'cashier':
                return '/plate/cashier/dashboard';
            default:
                return '/plate/';
        }
    }

    // Protected route guard
    async requireAuth(allowedRoles = []) {
        const isValid = await this.checkAuth();
        
        if (!isValid) {
            window.location.href = '/plate/login';
            return false;
        }

        if (allowedRoles.length > 0 && !allowedRoles.includes(this.getUserRole())) {
            window.location.href = '/plate/unauthorized';
            return false;
        }

        return true;
    }
}

// Create global auth instance
const auth = new AuthManager();

// Add logout button handler to all pages
document.addEventListener('DOMContentLoaded', () => {
    const logoutButtons = document.querySelectorAll('.logout-btn, #logoutButton');
    logoutButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            auth.logout();
        });
    });
});