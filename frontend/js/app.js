const API_BASE = "https://smartpesa-api.onrender.com";
console.log('App starting');
console.log('API:', API_BASE);

document.getElementById('login-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    try {
        const res = await fetch(API_BASE + '/users/login', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password})
        });
        const data = await res.json();
        if (res.ok) {
            localStorage.setItem('authToken', data.access_token);
            window.location.href = '/dashboard.html';
        } else alert('Login failed');
    } catch (err) {
        alert('Network error');
    }
});

document.getElementById('show-register')?.addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('login-screen').classList.remove('active');
    document.getElementById('register-screen').classList.add('active');
});

document.getElementById('show-login')?.addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('register-screen').classList.remove('active');
    document.getElementById('login-screen').classList.add('active');
});
