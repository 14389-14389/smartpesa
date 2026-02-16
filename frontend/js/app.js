// SmartPesa - Production Version
const API_BASE = "https://smartpesa-api.onrender.com";

console.log('🚀 SmartPesa initializing...');
console.log('API Base URL:', API_BASE);

let authToken = localStorage.getItem('authToken');
let currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
let currentBusinessId = localStorage.getItem('currentBusinessId');
let charts = {};

// DOM Elements
const loginScreen = document.getElementById('login-screen');
const registerScreen = document.getElementById('register-screen');
const dashboardScreen = document.getElementById('dashboard-screen');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const navItems = document.querySelectorAll('.nav-item');
const menuToggle = document.getElementById('menu-toggle');
const sidebar = document.getElementById('sidebar');
const pageTitle = document.getElementById('page-title');
const views = document.querySelectorAll('.view');
const userName = document.getElementById('user-name');
const userEmail = document.getElementById('user-email');
const logoutBtn = document.getElementById('logout-btn');
const businessSelect = document.getElementById('business-select');
const refreshBtn = document.getElementById('refresh-data');

// Helper function
function $(id) {
    return document.getElementById(id);
}

// Format as Kenyan Shillings
function formatKES(amount) {
    if (amount === undefined || amount === null) return 'KES 0';
    return 'KES ' + Math.round(amount).toLocaleString();
}

// Format date
function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-KE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Show toast notification
function showToast(message, type = 'success') {
    alert(message);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');
    console.log('Auth token exists:', !!authToken);
    console.log('Current user:', currentUser);
    
    if (authToken && currentUser.email) {
        console.log('Already logged in, showing dashboard');
        showDashboard();
        loadUserData();
    } else {
        console.log('Not logged in, showing login');
        showLogin();
    }
    
    setupEventListeners();
});

function setupEventListeners() {
    // Auth toggles
    $('show-register')?.addEventListener('click', (e) => {
        e.preventDefault();
        showRegister();
    });
    
    $('show-login')?.addEventListener('click', (e) => {
        e.preventDefault();
        showLogin();
    });
    
    // Forms
    loginForm?.addEventListener('submit', handleLogin);
    registerForm?.addEventListener('submit', handleRegister);
    
    // Navigation
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.dataset.view;
            console.log('Nav clicked:', view);
            switchView(view);
        });
    });
    
    // Menu toggle for mobile
    menuToggle?.addEventListener('click', () => {
        sidebar.classList.toggle('active');
    });
    
    // Logout
    logoutBtn?.addEventListener('click', handleLogout);
    
    // Business selector
    businessSelect?.addEventListener('change', (e) => {
        currentBusinessId = e.target.value;
        localStorage.setItem('currentBusinessId', currentBusinessId);
        console.log('Business selected:', currentBusinessId);
        loadUserData();
    });
    
    // Refresh button
    refreshBtn?.addEventListener('click', () => {
        loadUserData();
        showToast('Data refreshed!');
    });
}

// Authentication
async function handleLogin(e) {
    e.preventDefault();
    
    const email = $('email')?.value;
    const password = $('password')?.value;
    
    console.log('Login attempt with email:', email);
    console.log('Using API URL:', API_BASE);
    
    try {
        const res = await fetch(`${API_BASE}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await res.json();
        console.log('Login response:', data);
        
        if (res.ok) {
            authToken = data.access_token;
            currentUser = { email };
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            console.log('Login successful, token saved');
            showToast('Login successful!');
            
            showDashboard();
            await loadUserData();
            
        } else {
            showToast('Login failed: ' + (data.detail || 'Unknown error'), 'error');
        }
    } catch (err) {
        console.error('Login error:', err);
        showToast('Network error - is backend running?', 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const email = $('reg-email')?.value;
    const password = $('reg-password')?.value;
    const confirm = $('reg-confirm')?.value;
    
    if (password !== confirm) {
        showToast('Passwords do not match', 'error');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/users/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (res.ok) {
            showToast('Registration successful! Please login.');
            showLogin();
        } else {
            const data = await res.json();
            showToast('Registration failed: ' + (data.detail || 'Unknown error'), 'error');
        }
    } catch (err) {
        console.error('Registration error:', err);
        showToast('Network error', 'error');
    }
}

function handleLogout() {
    localStorage.clear();
    authToken = null;
    currentUser = {};
    currentBusinessId = null;
    showLogin();
    showToast('Logged out');
}

// UI Navigation
function showLogin() {
    console.log('Showing login');
    loginScreen.classList.add('active');
    registerScreen.classList.remove('active');
    dashboardScreen.classList.remove('active');
}

function showRegister() {
    console.log('Showing register');
    registerScreen.classList.add('active');
    loginScreen.classList.remove('active');
    dashboardScreen.classList.remove('active');
}

function showDashboard() {
    console.log('Showing dashboard');
    dashboardScreen.classList.add('active');
    loginScreen.classList.remove('active');
    registerScreen.classList.remove('active');
    
    if (userName) userName.textContent = currentUser.email?.split('@')[0] || 'User';
    if (userEmail) userEmail.textContent = currentUser.email || 'user@example.com';
}

function switchView(viewName) {
    console.log('Switching to view:', viewName);
    
    // Update navigation
    navItems.forEach(item => {
        item.classList.remove('active');
        if (item.dataset.view === viewName) {
            item.classList.add('active');
        }
    });
    
    // Update title
    const titles = {
        dashboard: 'Dashboard',
        transactions: 'Transactions',
        forecast: 'Forecast',
        inventory: 'Inventory',
        businesses: 'Businesses',
        risk: 'Risk Analysis'
    };
    if (pageTitle) pageTitle.textContent = titles[viewName] || 'Dashboard';
    
    // Hide all views
    views.forEach(v => v.classList.remove('active'));
    
    // Show selected view
    const selectedView = $(`${viewName}-view`);
    if (selectedView) {
        selectedView.classList.add('active');
    }
}

// Data Loading with Authentication
async function fetchWithAuth(url, options = {}) {
    if (!authToken) {
        console.error('No auth token available');
        showLogin();
        throw new Error('Not authenticated');
    }
    
    const response = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${authToken}`
        }
    });
    
    if (response.status === 401) {
        console.error('Authentication failed');
        localStorage.clear();
        authToken = null;
        showLogin();
        throw new Error('Session expired');
    }
    
    return response;
}

async function loadUserData() {
    console.log('Loading user data...');
    try {
        await loadBusinesses();
        if (currentBusinessId) {
            loadDashboard();
            loadForecast();
            loadRiskAnalysis();
            loadInventory();
        }
    } catch (err) {
        console.error('Error loading user data:', err);
    }
}

async function loadBusinesses() {
    try {
        console.log('Fetching businesses...');
        const response = await fetchWithAuth(`${API_BASE}/businesses/`);
        const businesses = await response.json();
        console.log('Businesses loaded:', businesses);
        
        // Update selector
        if (businessSelect) {
            businessSelect.innerHTML = '<option value="">Select Business</option>';
            if (Array.isArray(businesses) && businesses.length > 0) {
                businesses.forEach(b => {
                    const opt = document.createElement('option');
                    opt.value = b.id;
                    opt.textContent = b.name;
                    if (b.id == currentBusinessId) opt.selected = true;
                    businessSelect.appendChild(opt);
                });
            }
        }
        
        // Set default
        if (!currentBusinessId && Array.isArray(businesses) && businesses.length > 0) {
            currentBusinessId = businesses[0].id;
            localStorage.setItem('currentBusinessId', currentBusinessId);
            if (businessSelect) businessSelect.value = currentBusinessId;
        }
        
        // Update businesses grid
        const grid = $('businesses-grid');
        if (grid) {
            if (!Array.isArray(businesses) || businesses.length === 0) {
                grid.innerHTML = '<div class="loading-spinner">No businesses found. Create one first.</div>';
            } else {
                grid.innerHTML = businesses.map(b => `
                    <div class="business-card" onclick="selectBusiness(${b.id})">
                        <h3>${b.name}</h3>
                        <p><i class="fas fa-calendar"></i> Created: ${new Date(b.created_at).toLocaleDateString()}</p>
                        <p><i class="fas fa-id-card"></i> ID: ${b.id}</p>
                        <span class="badge ${b.id == currentBusinessId ? 'income' : ''}">
                            ${b.id == currentBusinessId ? '✓ Selected' : 'Click to select'}
                        </span>
                    </div>
                `).join('');
            }
        }
    } catch (err) {
        console.error('Error loading businesses:', err);
    }
}

// Global function for business selection
window.selectBusiness = function(id) {
    currentBusinessId = id;
    localStorage.setItem('currentBusinessId', id);
    if (businessSelect) businessSelect.value = id;
    loadUserData();
    showToast(`Business ${id} selected`);
};

// Dashboard Functions
async function loadDashboard() {
    if (!currentBusinessId) return;
    
    try {
        console.log('Loading dashboard for business:', currentBusinessId);
        
        const summary = await fetchWithAuth(
            `${API_BASE}/transactions/summary/overview?business_id=${currentBusinessId}&days=30`
        );
        const summaryData = await summary.json();
        
        if ($('total-income')) $('total-income').textContent = formatKES(summaryData.total_income || 0);
        if ($('total-expense')) $('total-expense').textContent = formatKES(summaryData.total_expense || 0);
        if ($('net-cashflow')) $('net-cashflow').textContent = formatKES(summaryData.net_cashflow || 0);
        
    } catch (err) {
        console.error('Error loading dashboard:', err);
    }
}

async function loadForecast() {
    if (!currentBusinessId) return;
    console.log('Forecast loaded');
}

async function loadRiskAnalysis() {
    if (!currentBusinessId) return;
    console.log('Risk analysis loaded');
}

async function loadInventory() {
    if (!currentBusinessId) return;
    console.log('Inventory loaded');
}

console.log('✅ SmartPesa initialized');
