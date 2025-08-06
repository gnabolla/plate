// Login page specific functionality

document.addEventListener('DOMContentLoaded', () => {
    // Check if already logged in
    if (auth.isAuthenticated()) {
        window.location.href = auth.getRedirectUrl();
        return;
    }

    // Get form elements
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const rememberMeCheckbox = document.getElementById('rememberMe');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    const loginButton = document.getElementById('loginButton');
    const buttonText = loginButton.querySelector('.button-text');
    const loadingSpinner = loginButton.querySelector('.loading-spinner');
    const loadingOverlay = document.getElementById('loadingOverlay');

    // Check for remembered username
    const rememberedUsername = localStorage.getItem('remembered_username');
    if (rememberedUsername) {
        usernameInput.value = rememberedUsername;
        rememberMeCheckbox.checked = true;
    }

    // Handle form submission
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Clear any previous errors
        hideError();
        
        // Get form values
        const username = usernameInput.value.trim();
        const password = passwordInput.value;
        
        // Basic validation
        if (!username || !password) {
            showError('Please enter both username and password');
            return;
        }
        
        // Show loading state
        setLoading(true);
        
        try {
            // Attempt login
            const result = await auth.login(username, password);
            
            if (result.success) {
                // Handle remember me
                if (rememberMeCheckbox.checked) {
                    localStorage.setItem('remembered_username', username);
                } else {
                    localStorage.removeItem('remembered_username');
                }
                
                // Show success briefly
                showSuccess('Login successful! Redirecting...');
                
                // Redirect based on role
                setTimeout(() => {
                    window.location.href = auth.getRedirectUrl();
                }, 1000);
            } else {
                // Show error
                showError(result.error || 'Invalid username or password');
                setLoading(false);
            }
        } catch (error) {
            showError('An unexpected error occurred. Please try again.');
            setLoading(false);
        }
    });

    // Helper functions
    function setLoading(isLoading) {
        if (isLoading) {
            loginButton.disabled = true;
            buttonText.style.display = 'none';
            loadingSpinner.style.display = 'inline-block';
            usernameInput.disabled = true;
            passwordInput.disabled = true;
        } else {
            loginButton.disabled = false;
            buttonText.style.display = 'inline';
            loadingSpinner.style.display = 'none';
            usernameInput.disabled = false;
            passwordInput.disabled = false;
        }
    }

    function showError(message) {
        errorText.textContent = message;
        errorMessage.style.display = 'flex';
        errorMessage.classList.remove('success-message');
        errorMessage.classList.add('error-message');
    }

    function showSuccess(message) {
        errorText.textContent = message;
        errorMessage.style.display = 'flex';
        errorMessage.classList.remove('error-message');
        errorMessage.classList.add('success-message');
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }

    // Handle Enter key on inputs
    [usernameInput, passwordInput].forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                loginForm.dispatchEvent(new Event('submit'));
            }
        });
    });
});

// Toggle password visibility
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.getElementById('toggleIcon');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.classList.remove('fa-eye');
        toggleIcon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        toggleIcon.classList.remove('fa-eye-slash');
        toggleIcon.classList.add('fa-eye');
    }
}

// Fill credentials for testing
function fillCredentials(username, password) {
    document.getElementById('username').value = username;
    document.getElementById('password').value = password;
    document.getElementById('username').focus();
}

// Add success message styles dynamically
const style = document.createElement('style');
style.textContent = `
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    
    .success-message i {
        color: #155724;
    }
`;
document.head.appendChild(style);