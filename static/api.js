// API utility for backend communication

class API {
    constructor() {
        this.baseUrl = '/plate/api';
    }
    
    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        // Add auth headers
        const headers = {
            ...auth.getAuthHeaders(),
            ...options.headers
        };
        
        try {
            const response = await fetch(url, {
                ...options,
                headers
            });
            
            // Handle unauthorized
            if (response.status === 401) {
                auth.clearAuth();
                window.location.href = '/plate/login';
                return;
            }
            
            // Handle other errors
            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
                throw new Error(error.detail || `HTTP error! status: ${response.status}`);
            }
            
            // Return JSON response
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    // GET request
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        return this.request(url, {
            method: 'GET'
        });
    }
    
    // POST request
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
    }
    
    // PUT request
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
    }
    
    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
    
    // Violation endpoints
    violations = {
        create: (data) => this.post('/violations', data),
        list: (params) => this.get('/violations', params),
        getByTicket: (ticketNumber) => this.get(`/violations/ticket/${ticketNumber}`),
        updateStatus: (id, status) => this.put(`/violations/${id}/status`, { status })
    };
    
    // Payment endpoints
    payments = {
        create: (data) => this.post('/payments', data),
        list: (params) => this.get('/payments', params)
    };
    
    // User endpoints
    users = {
        create: (data) => this.post('/users', data),
        list: () => this.get('/users'),
        update: (id, data) => this.put(`/users/${id}`, data),
        delete: (id) => this.delete(`/users/${id}`),
        changePassword: (id, data) => this.put(`/users/${id}/password`, data)
    };
    
    // Appeal endpoints
    appeals = {
        create: (data) => this.post('/appeals', data),
        list: (params) => this.get('/appeals', params),
        updateStatus: (id, status, reviewNotes) => this.put(`/appeals/${id}/status`, { status, review_notes: reviewNotes })
    };
    
    // Dashboard statistics
    dashboard = {
        getStats: () => this.get('/dashboard/statistics')
    };
    
    // Owner endpoints
    owners = {
        create: (data) => this.post('/owners', data),
        list: () => this.get('/owners')
    };
    
    // Vehicle endpoints
    vehicles = {
        create: (data) => this.post('/vehicles', data),
        list: () => this.get('/vehicles'),
        getByPlate: (plateNumber) => this.get(`/vehicles/plate/${plateNumber}`)
    };
    
    // Violation types
    violationTypes = {
        list: () => this.get('/violation-types')
    };
}

// Create global API instance
window.api = new API();

// Helper function to handle API errors with toast notifications
window.handleApiError = function(error, defaultMessage = 'An error occurred') {
    const message = error.message || defaultMessage;
    dashboardUtils.toast.error(message);
    console.error('API Error:', error);
};

// Helper function to handle form submissions
window.handleFormSubmit = async function(formId, apiCall, successMessage, onSuccess) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Show loading
        dashboardUtils.loading.show('Processing...');
        
        try {
            // Make API call
            const result = await apiCall(data);
            
            // Show success message
            dashboardUtils.toast.success(successMessage);
            
            // Call success callback
            if (onSuccess) {
                onSuccess(result);
            }
            
            // Reset form
            form.reset();
        } catch (error) {
            handleApiError(error);
        } finally {
            dashboardUtils.loading.hide();
        }
    });
};