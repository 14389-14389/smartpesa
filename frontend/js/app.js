const API_BASE = "https://smartpesa-api.onrender.com";

console.log('SmartPesa starting...');
console.log('API URL:', API_BASE);

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // Login form handler
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            try {
                const res = await fetch(API_BASE + '/users/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                
                const data = await res.json();
                
                if (res.ok) {
                    localStorage.setItem('authToken', data.access_token);
                    alert('Login successful!');
                    window.location.href = '/dashboard.html';
                } else {
                    alert('Error: ' + (data.detail || 'Login failed'));
                }
            } catch (err) {
                alert('Network error - backend may be down');
            }
        });
    }
    
    // Register link
    document.getElementById('show-register')?.addEventListener('click', function(e) {
        e.preventDefault();
        document.getElementById('login-screen').classList.remove('active');
        document.getElementById('register-screen').classList.add('active');
    });
    
    // Login link
    document.getElementById('show-login')?.addEventListener('click', function(e) {
        e.preventDefault();
        document.getElementById('register-screen').classList.remove('active');
        document.getElementById('login-screen').classList.add('active');
    });
});
