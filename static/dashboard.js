// Dashboard common functionality

// Sidebar toggle
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.getElementById('menuToggle');
    
    // Toggle sidebar
    menuToggle?.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        
        // Save preference
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
    
    // Restore sidebar state
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isCollapsed) {
        sidebar.classList.add('collapsed');
    }
    
    // Mobile sidebar handling
    if (window.innerWidth <= 768) {
        sidebar.classList.add('mobile');
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
                sidebar.classList.remove('mobile-open');
            }
        });
    }
    
    // User dropdown
    const userMenuToggle = document.querySelector('.user-menu-toggle');
    const userDropdown = document.querySelector('.user-dropdown');
    
    userMenuToggle?.addEventListener('click', (e) => {
        e.stopPropagation();
        userDropdown.style.display = userDropdown.style.display === 'none' ? 'block' : 'none';
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
        if (userDropdown) {
            userDropdown.style.display = 'none';
        }
    });
    
    // Set active navigation item
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

// Toast notification system
const toast = {
    show(message, type = 'info', duration = 5000) {
        const toastContainer = document.getElementById('toastContainer');
        
        const toastElement = document.createElement('div');
        toastElement.className = `toast ${type}`;
        
        const icon = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        }[type] || 'fa-info-circle';
        
        toastElement.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" style="margin-left: auto; background: none; border: none; cursor: pointer;">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        toastContainer.appendChild(toastElement);
        
        // Auto remove after duration
        setTimeout(() => {
            toastElement.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toastElement.remove(), 300);
        }, duration);
    },
    
    success(message, duration) {
        this.show(message, 'success', duration);
    },
    
    error(message, duration) {
        this.show(message, 'error', duration);
    },
    
    warning(message, duration) {
        this.show(message, 'warning', duration);
    },
    
    info(message, duration) {
        this.show(message, 'info', duration);
    }
};

// Loading overlay helpers
const loading = {
    show(message = 'Loading...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingText = overlay.querySelector('p');
        loadingText.textContent = message;
        overlay.style.display = 'flex';
    },
    
    hide() {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = 'none';
    }
};

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

// Debounce function for search inputs
function debounce(func, wait) {
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

// Export utilities
window.dashboardUtils = {
    toast,
    loading,
    formatCurrency,
    formatDate,
    debounce
};

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Profile and Settings placeholders
window.showProfile = function() {
    alert('Profile page not available in simplified version');
};

window.showSettings = function() {
    alert('Settings page not available in simplified version');
};