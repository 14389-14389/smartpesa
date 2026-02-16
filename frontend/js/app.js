// SmartPesa - Clean Version
const API_BASE = "https://smartpesa-api.onrender.com";

console.log('🚀 SmartPesa starting...');
console.log('API URL:', API_BASE);

// Login function
async function login() {
    const email = document.getElementById('email')?.value || 'test@example.com';
    const password = document.getElementById('password')?.value || 'password123';
    
    try {
        const res = await fetch(`${API_BASE}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            localStorage.setItem('authToken', data.access_token);
            localStorage.setItem('currentUser', JSON.stringify({ email }));
            window.location.href = '/dashboard.html';
        } else {
            alert('Login failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (err) {
        alert('Network error - backend not reachable');
    }
}

// Register function
async function register() {
    const email = document.getElementById('reg-email')?.value;
    const password = document.getElementById('reg-password')?.value;
    const confirm = document.getElementById('reg-confirm')?.value;
    
    if (password !== confirm) {
        alert('Passwords do not match');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/users/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (res.ok) {
            alert('Registration successful! Please login.');
            showLogin();
        } else {
            const data = await res.json();
            alert('Registration failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (err) {
        alert('Network error');
    }
}

// Logout function
function logout() {
    localStorage.clear();
    window.location.href = '/';
}

// Show login screen
function showLogin() {
    document.getElementById('login-screen').classList.add('active');
    document.getElementById('register-screen').classList.remove('active');
    document.getElementById('dashboard-screen').classList.remove('active');
}

// Show register screen
function showRegister() {
    document.getElementById('register-screen').classList.add('active');
    document.getElementById('login-screen').classList.remove('active');
    document.getElementById('dashboard-screen').classList.remove('active');
}

// Check login status on page load
document.addEventListener('DOMContentLoaded', () => {
    // Setup event listeners
    document.getElementById('login-form')?.addEventListener('submit', (e) => {
        e.preventDefault();
        login();
    });
    
    document.getElementById('register-form')?.addEventListener('submit', (e) => {
        e.preventDefault();
        register();
    });
    
    document.getElementById('show-register')?.addEventListener('click', (e) => {
        e.preventDefault();
        showRegister();
    });
    
    document.getElementById('show-login')?.addEventListener('click', (e) => {
        e.preventDefault();
        showLogin();
    });
    
    // If already logged in, go to dashboard
    if (localStorage.getItem('authToken')) {
        window.location.href = '/dashboard.html';
    }
});

console.log('✅ SmartPesa ready');
