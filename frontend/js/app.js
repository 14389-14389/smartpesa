// SmartPesa - Working Version
const API_BASE = "https://smartpesa-api.onrender.com";

console.log('🚀 SmartPesa starting...');
console.log('API URL:', API_BASE);

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    
    // Get form elements
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    console.log('Login form found:', !!loginForm);
    console.log('Register form found:', !!registerForm);
    
    // Login form handler
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Login form submitted');
            
            const email = document.getElementById('email')?.value;
            const password = document.getElementById('password')?.value;
            
            console.log('Email:', email);
            console.log('Password length:', password?.length);
            
            if (!email || !password) {
                alert('Please enter email and password');
                return;
            }
            
            try {
                console.log('Sending login request to:', `${API_BASE}/users/login`);
                
                const response = await fetch(`${API_BASE}/users/login`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ email, password })
                });
                
                console.log('Response status:', response.status);
                
                const data = await response.json();
                console.log('Response data:', data);
                
                if (response.ok) {
                    console.log('Login successful! Token:', data.access_token?.substring(0, 20) + '...');
                    localStorage.setItem('authToken', data.access_token);
                    localStorage.setItem('currentUser', JSON.stringify({ email }));
                    alert('Login successful! Redirecting...');
                    window.location.href = '/dashboard.html';
                } else {
                    alert('Login failed: ' + (data.detail || 'Unknown error'));
                }
            } catch (error) {
                console.error('Fetch error:', error);
                alert('Network error - cannot connect to backend. Check console for details.');
            }
        });
    } else {
        console.error('Login form not found!');
    }
    
    // Register form handler
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Register form submitted');
            
            const email = document.getElementById('reg-email')?.value;
            const password = document.getElementById('reg-password')?.value;
            const confirm = document.getElementById('reg-confirm')?.value;
            
            if (!email || !password || !confirm) {
                alert('Please fill all fields');
                return;
            }
            
            if (password !== confirm) {
                alert('Passwords do not match');
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/users/register`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ email, password })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alert('Registration successful! Please login.');
                    // Switch to login screen
                    document.getElementById('login-screen').classList.add('active');
                    document.getElementById('register-screen').classList.remove('active');
                } else {
                    alert('Registration failed: ' + (data.detail || 'Unknown error'));
                }
            } catch (error) {
                console.error('Registration error:', error);
                alert('Network error - cannot connect to backend');
            }
        });
    }
    
    // Toggle between login and register
    document.getElementById('show-register')?.addEventListener('click', function(e) {
        e.preventDefault();
        document.getElementById('login-screen').classList.remove('active');
        document.getElementById('register-screen').classList.add('active');
    });
    
    document.getElementById('show-login')?.addEventListener('click', function(e) {
        e.preventDefault();
        document.getElementById('register-screen').classList.remove('active');
        document.getElementById('login-screen').classList.add('active');
    });
    
    // Check if already logged in
    if (localStorage.getItem('authToken')) {
        console.log('Already logged in, redirecting to dashboard');
        window.location.href = '/dashboard.html';
    }
});

console.log('✅ SmartPesa ready - waiting for events');
