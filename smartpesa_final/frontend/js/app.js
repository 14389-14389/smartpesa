const API_BASE = "http://localhost:8000/api/v1";
let currentBusinessId = localStorage.getItem('currentBusinessId') || null;
let authToken = localStorage.getItem('authToken');
let currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

console.log('🚀 SmartPesa starting...');
console.log('API URL:', API_BASE);
console.log('Current Business ID:', currentBusinessId);
console.log('Auth Token:', authToken ? 'Present' : 'Not present');

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: white;
        border-left: 4px solid ${type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : '#3B82F6'};
        border-radius: 8px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        z-index: 9999;
        animation: slideIn 0.3s ease;
        font-family: 'Inter', sans-serif;
    `;
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}" 
               style="color: ${type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : '#3B82F6'}; font-size: 20px;"></i>
            <span style="color: #1e293b; font-weight: 500;">${message}</span>
        </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// API call helper
async function apiCall(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(authToken && { 'Authorization': `Bearer ${authToken}` })
        }
    };
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, { ...defaultOptions, ...options });
        
        if (response.status === 401) {
            localStorage.clear();
            if (!window.location.pathname.includes('index.html')) {
                window.location.href = '/index.html';
            }
            return null;
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API Error:', error);
        showToast('Network error - backend unreachable', 'error');
        return null;
    }
}

// Format currency
function formatKES(amount) {
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES',
        minimumFractionDigits: 2
    }).format(amount || 0);
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-KE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// ==================== AUTHENTICATION ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // Check if on login page
    if (window.location.pathname.includes('index.html') || window.location.pathname === '/') {
        console.log('On login page');
        
        // If already logged in, go to dashboard
        if (authToken) {
            window.location.href = '/dashboard.html';
            return;
        }
        
        // Login form handler
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                const loginBtn = e.target.querySelector('button[type="submit"]');
                
                const originalText = loginBtn.innerHTML;
                loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
                loginBtn.disabled = true;
                
                try {
                    const response = await fetch(`${API_BASE}/users/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, password })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        localStorage.setItem('authToken', data.access_token);
                        localStorage.setItem('currentUser', JSON.stringify({ email }));
                        authToken = data.access_token;
                        
                        showToast('Login successful! Redirecting...', 'success');
                        
                        setTimeout(() => {
                            window.location.href = '/dashboard.html';
                        }, 1000);
                    } else {
                        showToast(data.detail || 'Login failed', 'error');
                        loginBtn.innerHTML = originalText;
                        loginBtn.disabled = false;
                    }
                } catch (err) {
                    showToast('Network error - backend unreachable', 'error');
                    loginBtn.innerHTML = originalText;
                    loginBtn.disabled = false;
                }
            });
        }
        
        // Toggle between login and register screens
        const showRegister = document.getElementById('show-register');
        if (showRegister) {
            showRegister.addEventListener('click', (e) => {
                e.preventDefault();
                document.getElementById('login-screen').classList.remove('active');
                document.getElementById('register-screen').classList.add('active');
            });
        }
        
        const showLogin = document.getElementById('show-login');
        if (showLogin) {
            showLogin.addEventListener('click', (e) => {
                e.preventDefault();
                document.getElementById('register-screen').classList.remove('active');
                document.getElementById('login-screen').classList.add('active');
            });
        }
    }
    
    // Check if on dashboard page
    if (window.location.pathname.includes('dashboard.html')) {
        console.log('On dashboard page');
        
        // Check authentication
        if (!authToken) {
            window.location.href = '/index.html';
            return;
        }
        
        // Set user info from localStorage
        const userName = document.getElementById('user-name');
        const userEmail = document.getElementById('user-email');
        const userAvatar = document.getElementById('user-avatar');
        
        if (userName && currentUser.email) {
            userName.textContent = currentUser.email.split('@')[0];
        }
        if (userEmail && currentUser.email) {
            userEmail.textContent = currentUser.email;
        }
        if (userAvatar && currentUser.email) {
            userAvatar.textContent = currentUser.email[0].toUpperCase();
        }
        
        // Load dashboard data
        setTimeout(() => {
            loadDashboardData();
        }, 500);
        
        // Set up logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', logout);
        }
        
        // Set up refresh button
        const refreshBtn = document.getElementById('refresh-data');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                loadDashboardData();
                showToast('Data refreshed', 'success');
            });
        }
    }
});

// ==================== DASHBOARD FUNCTIONS ====================
async function loadDashboardData() {
    console.log('Loading dashboard data...');
    
    // Get current user info from API
    const userInfo = await apiCall('/users/me');
    if (userInfo) {
        document.getElementById('user-name').textContent = userInfo.full_name || userInfo.email.split('@')[0];
        document.getElementById('user-email').textContent = userInfo.email;
        document.getElementById('user-avatar').textContent = (userInfo.full_name || userInfo.email)[0].toUpperCase();
        
        // Update currentUser in localStorage
        currentUser = userInfo;
        localStorage.setItem('currentUser', JSON.stringify(userInfo));
    }
    
    // Load businesses
    await loadBusinesses();
    
    if (currentBusinessId) {
        // Load summary data
        await loadSummaryData();
        
        // Load recent transactions
        await loadRecentTransactions();
        
        // Load inventory alerts
        await loadInventoryAlerts();
        
        // Load charts
        await loadCharts();
    }
}

// ==================== BUSINESS FUNCTIONS ====================
async function loadBusinesses() {
    console.log('📊 Loading businesses...');
    
    try {
        const businesses = await apiCall('/businesses/');
        console.log('Businesses loaded:', businesses);
        
        // Update business selector dropdown
        updateBusinessSelector(businesses);
        
        // Update businesses view
        updateBusinessesView(businesses);
        
        // Update current business ID
        updateCurrentBusinessId(businesses);
        
        return businesses || [];
    } catch (error) {
        console.error('Error loading businesses:', error);
        return [];
    }
}

function updateBusinessSelector(businesses) {
    const select = document.getElementById('business-select');
    if (!select) {
        console.log('Business select element not found');
        return;
    }
    
    select.innerHTML = '<option value="">Select Business</option>';
    
    if (businesses && businesses.length > 0) {
        businesses.forEach(b => {
            const option = document.createElement('option');
            option.value = b.id;
            option.textContent = b.name;
            if (b.id == currentBusinessId) {
                option.selected = true;
            }
            select.appendChild(option);
        });
        console.log('✅ Business dropdown updated with', businesses.length, 'businesses');
    } else {
        console.log('No businesses to display in dropdown');
    }
    
    // Add change event listener (remove existing first)
    select.removeEventListener('change', handleBusinessChange);
    select.addEventListener('change', handleBusinessChange);
}

function handleBusinessChange(e) {
    if (e.target.value) {
        currentBusinessId = e.target.value;
        localStorage.setItem('currentBusinessId', currentBusinessId);
        loadDashboardData();
        showToast(`Switched to ${e.target.options[e.target.selectedIndex].text}`, 'success');
    }
}

function updateBusinessesView(businesses) {
    const container = document.getElementById('businesses-grid');
    if (!container) {
        console.log('Businesses grid container not found');
        return;
    }
    
    if (!businesses || businesses.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 40px; grid-column: 1/-1;">No businesses found. Click "Add Business" to create one.</div>';
        return;
    }
    
    let html = '';
    businesses.forEach(business => {
        const createdDate = business.created_at ? new Date(business.created_at).toLocaleDateString() : 'N/A';
        const isActive = business.is_active ? 'Active' : 'Inactive';
        const activeClass = business.is_active ? 'badge good-stock' : 'badge low-stock';
        
        html += `
            <div class="business-card" onclick="selectBusiness(${business.id})">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h3>${business.name}</h3>
                    <span class="${activeClass}">${isActive}</span>
                </div>
                <p><i class="fas fa-tag"></i> ${business.type || 'Not specified'}</p>
                <p><i class="fas fa-calendar"></i> Created: ${createdDate}</p>
                <p><i class="fas fa-money-bill-wave"></i> Currency: ${business.currency || 'KES'}</p>
            </div>
        `;
    });
    
    container.innerHTML = html;
    console.log('✅ Businesses view updated with', businesses.length, 'businesses');
}

function updateCurrentBusinessId(businesses) {
    if (!businesses || businesses.length === 0) {
        currentBusinessId = null;
        localStorage.removeItem('currentBusinessId');
        return;
    }
    
    const select = document.getElementById('business-select');
    
    // If no business selected or selected business doesn't exist, select first one
    if (!currentBusinessId || !businesses.some(b => b.id == currentBusinessId)) {
        currentBusinessId = businesses[0].id;
        localStorage.setItem('currentBusinessId', currentBusinessId);
    }
    
    // Update dropdown selection
    if (select) {
        select.value = currentBusinessId;
    }
    
    console.log('Current business ID:', currentBusinessId);
}

window.selectBusiness = function(businessId) {
    console.log('Selecting business:', businessId);
    currentBusinessId = businessId;
    localStorage.setItem('currentBusinessId', businessId);
    
    const select = document.getElementById('business-select');
    if (select) {
        select.value = businessId;
    }
    
    showToast('Business selected', 'success');
    
    // Reload dashboard data
    loadDashboardData();
};

async function saveBusiness(event) {
    if (event) {
        event.preventDefault();
    }
    
    console.log('💼 Creating new business...');
    
    const businessName = document.getElementById('business-name')?.value;
    const businessType = document.getElementById('business-type')?.value || 'retail';
    const businessCurrency = document.getElementById('business-currency')?.value || 'KES';

    if (!businessName) {
        showToast('Please enter business name', 'error');
        return false;
    }

    const token = localStorage.getItem('authToken');
    if (!token) {
        showToast('You are not logged in', 'error');
        window.location.href = '/index.html';
        return false;
    }

    try {
        const response = await fetch(`${API_BASE}/businesses/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                name: businessName,
                type: businessType,
                currency: businessCurrency
            })
        });

        const data = await response.json();
        console.log('Create business response:', data);

        if (response.ok) {
            showToast('Business created successfully!', 'success');
            closeModal('business-modal');
            
            // Reset form
            document.getElementById('business-name').value = '';
            
            // Reload businesses
            await loadBusinesses();
            
            // If this is the first business, set as current
            if (!currentBusinessId && data.id) {
                currentBusinessId = data.id;
                localStorage.setItem('currentBusinessId', data.id);
            }
            
            // Switch to businesses view to show the new business
            if (typeof switchView === 'function') {
                switchView('businesses');
            }
            
            return true;
        } else {
            showToast(data.detail || 'Failed to create business', 'error');
            return false;
        }
    } catch (error) {
        console.error('Error creating business:', error);
        showToast('Error creating business: ' + (error.message || 'Unknown error'), 'error');
        return false;
    }
}

// ==================== SUMMARY FUNCTIONS ====================
async function loadSummaryData() {
    if (!currentBusinessId) return;
    
    try {
        const summary = await apiCall(`/transactions/summary/overview?business_id=${currentBusinessId}&days=30`);
        
        if (summary) {
            // Update KPI cards
            const incomeEl = document.getElementById('total-income');
            const expenseEl = document.getElementById('total-expense');
            const netEl = document.getElementById('net-cashflow');
            
            if (incomeEl) incomeEl.textContent = formatKES(summary.total_income || 0);
            if (expenseEl) expenseEl.textContent = formatKES(summary.total_expense || 0);
            if (netEl) netEl.textContent = formatKES(summary.net_cashflow || 0);
            
            console.log('✅ Summary data loaded:', summary);
        }
    } catch (error) {
        console.error('Error loading summary:', error);
    }
}

async function loadRecentTransactions() {
    if (!currentBusinessId) return;
    
    try {
        const transactions = await apiCall(`/transactions/?business_id=${currentBusinessId}&limit=5`);
        
        const tbody = document.getElementById('recent-transactions-body');
        if (!tbody) return;
        
        if (!transactions || transactions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">No transactions found</td></tr>';
            return;
        }
        
        let html = '';
        transactions.forEach(t => {
            html += `
                <tr>
                    <td>${formatDate(t.created_at)}</td>
                    <td>${t.description || '-'}</td>
                    <td>${t.category}</td>
                    <td>${formatKES(t.amount)}</td>
                    <td><span class="badge ${t.type}">${t.type}</span></td>
                    <td class="action-buttons">
                        <button class="action-btn-icon" onclick="editTransaction(${t.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn-icon" onclick="deleteTransaction(${t.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
        console.log('✅ Recent transactions loaded:', transactions.length);
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
}

async function loadInventoryAlerts() {
    if (!currentBusinessId) return;
    
    try {
        const inventory = await apiCall(`/inventory/?business_id=${currentBusinessId}`);
        
        if (!inventory) return;
        
        // Update inventory badge
        const badge = document.getElementById('inventory-badge');
        if (badge) {
            const lowStockCount = inventory.filter(i => i.quantity <= i.reorder_level).length;
            badge.textContent = lowStockCount;
        }
        
        // Find the low stock alerts table
        const tables = document.querySelectorAll('.transactions-table');
        if (tables.length >= 2) {
            const lowStockTable = tables[1].querySelector('tbody');
            if (lowStockTable) {
                const lowStockItems = inventory.filter(i => i.quantity <= i.reorder_level);
                
                if (lowStockItems.length === 0) {
                    lowStockTable.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">No low stock items</td></tr>';
                } else {
                    let html = '';
                    lowStockItems.forEach(item => {
                        html += `
                            <tr>
                                <td>${item.name}</td>
                                <td>${item.sku || '-'}</td>
                                <td>${item.quantity}</td>
                                <td>${item.reorder_level}</td>
                                <td><span class="badge low-stock">Low Stock</span></td>
                                <td class="action-buttons">
                                    <button class="action-btn-icon" onclick="editInventoryItem(${item.id})">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="action-btn-icon" onclick="restockInventoryItem(${item.id})">
                                        <i class="fas fa-plus-circle"></i>
                                    </button>
                                </td>
                            </tr>
                        `;
                    });
                    lowStockTable.innerHTML = html;
                }
            }
        }
        console.log('✅ Inventory alerts loaded:', inventory.length);
    } catch (error) {
        console.error('Error loading inventory:', error);
    }
}

async function loadCharts() {
    if (!currentBusinessId) return;
    
    try {
        // Get daily totals for cashflow chart
        const data = await apiCall(`/transactions/analysis/daily-totals?business_id=${currentBusinessId}&days=30`);
        
        // Create cashflow chart
        const ctx1 = document.getElementById('cashflow-chart')?.getContext('2d');
        if (ctx1 && data && data.length > 0) {
            // Destroy existing chart if it exists
            if (window.cashflowChart) window.cashflowChart.destroy();
            
            window.cashflowChart = new Chart(ctx1, {
                type: 'line',
                data: {
                    labels: data.map(d => {
                        const date = new Date(d.date);
                        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                    }),
                    datasets: [
                        {
                            label: 'Income',
                            data: data.map(d => d.income),
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: 'Expense',
                            data: data.map(d => d.expense),
                            borderColor: '#ef4444',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            tension: 0.4,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' }
                    }
                }
            });
        }
        
        // Get category data for pie chart
        const catData = await apiCall(`/transactions/analysis/by-category?business_id=${currentBusinessId}&days=30`);
        
        const ctx2 = document.getElementById('category-chart')?.getContext('2d');
        if (ctx2 && catData && catData.length > 0) {
            // Destroy existing chart if it exists
            if (window.categoryChart) window.categoryChart.destroy();
            
            // Take top 5 categories
            const topCats = catData.slice(0, 5);
            window.categoryChart = new Chart(ctx2, {
                type: 'doughnut',
                data: {
                    labels: topCats.map(c => c.category),
                    datasets: [{
                        data: topCats.map(c => c.total),
                        backgroundColor: ['#1e3c72', '#2a5298', '#3b6cb0', '#4b7ec9', '#5c8fd9'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }
        console.log('✅ Charts loaded');
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}

// ==================== INVENTORY FUNCTIONS ====================
async function saveInventoryItem() {
    currentBusinessId = localStorage.getItem('currentBusinessId');
    
    if (!currentBusinessId) {
        showToast('Please select a business first', 'error');
        return;
    }
    
    const item = {
        name: document.getElementById('inv-name').value,
        sku: document.getElementById('inv-sku').value || undefined,
        quantity: parseFloat(document.getElementById('inv-quantity').value) || 0,
        unit: document.getElementById('inv-unit').value,
        price_per_unit: parseFloat(document.getElementById('inv-price').value) || 0,
        reorder_level: parseFloat(document.getElementById('inv-reorder').value) || 10,
        business_id: parseInt(currentBusinessId)
    };

    console.log('Saving inventory item:', item);

    if (!item.name) {
        showToast('Please enter item name', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/inventory/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify(item)
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Inventory item added successfully', 'success');
            closeModal('inventory-modal');
            document.getElementById('inventory-form').reset();
            // Refresh the page to show new item
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.detail || 'Failed to add item', 'error');
        }
    } catch (error) {
        console.error('Error adding inventory:', error);
        showToast('Error adding item', 'error');
    }
}

// ==================== SUPPLIER FUNCTIONS ====================
async function saveSupplier() {
    currentBusinessId = localStorage.getItem('currentBusinessId');
    
    if (!currentBusinessId) {
        showToast('Please select a business first', 'error');
        return;
    }
    
    const supplier = {
        name: document.getElementById('sup-name').value,
        contact_person: document.getElementById('sup-contact').value || undefined,
        phone: document.getElementById('sup-phone').value || undefined,
        email: document.getElementById('sup-email').value || undefined,
        payment_terms: document.getElementById('sup-payment-terms').value || 'Net 30',
        business_id: parseInt(currentBusinessId)
    };

    console.log('Saving supplier:', supplier);

    if (!supplier.name) {
        showToast('Please enter supplier name', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/suppliers/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify(supplier)
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Supplier added successfully', 'success');
            closeModal('supplier-modal');
            document.getElementById('supplier-form').reset();
            // Refresh the page to show new supplier
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.detail || 'Failed to add supplier', 'error');
        }
    } catch (error) {
        console.error('Error adding supplier:', error);
        showToast('Error adding supplier', 'error');
    }
}

// ==================== TRANSACTION FUNCTIONS ====================
async function saveTransaction() {
    currentBusinessId = localStorage.getItem('currentBusinessId');
    
    if (!currentBusinessId) {
        showToast('Please select a business first', 'error');
        return;
    }
    
    const transaction = {
        amount: parseFloat(document.getElementById('tx-amount')?.value) || 0,
        type: document.getElementById('tx-type')?.value || 'income',
        category: document.getElementById('tx-category')?.value || 'Sales',
        description: document.getElementById('tx-description')?.value || '',
        business_id: parseInt(currentBusinessId)
    };

    if (!transaction.amount) {
        showToast('Please enter amount', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/transactions/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify(transaction)
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Transaction added successfully', 'success');
            closeModal('transaction-modal');
            document.getElementById('transaction-form')?.reset();
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.detail || 'Failed to add transaction', 'error');
        }
    } catch (error) {
        console.error('Error adding transaction:', error);
        showToast('Error adding transaction', 'error');
    }
}

// ==================== PAYMENT FUNCTIONS ====================
async function savePayment() {
    const paymentModal = document.getElementById('payment-modal');
    const supplierId = paymentModal?.dataset.supplierId;
    const amount = parseFloat(document.getElementById('payment-amount')?.value) || 0;
    const method = document.getElementById('payment-method')?.value || 'bank_transfer';
    const date = document.getElementById('payment-date')?.value;
    const notes = document.getElementById('payment-notes')?.value || '';

    if (!supplierId || !amount) {
        showToast('Please enter payment amount', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/suppliers/payments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify({
                supplier_id: parseInt(supplierId),
                amount: amount,
                method: method,
                payment_date: date,
                notes: notes
            })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Payment recorded successfully', 'success');
            closeModal('payment-modal');
            document.getElementById('payment-form')?.reset();
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.detail || 'Failed to record payment', 'error');
        }
    } catch (error) {
        console.error('Error recording payment:', error);
        showToast('Error recording payment', 'error');
    }
}

// ==================== MODAL HELPERS ====================
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// ==================== ATTACH EVENT LISTENERS ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Setting up event listeners...');
    
    // Only run these on dashboard page
    if (window.location.pathname.includes('dashboard.html')) {
        
        // Inventory form submission
        const inventoryForm = document.getElementById('inventory-form');
        if (inventoryForm) {
            inventoryForm.addEventListener('submit', function(e) {
                e.preventDefault();
                saveInventoryItem();
            });
            console.log(' Inventory form handler attached');
        }

        // Supplier form submission
        const supplierForm = document.getElementById('supplier-form');
        if (supplierForm) {
            supplierForm.addEventListener('submit', function(e) {
                e.preventDefault();
                saveSupplier();
            });
            console.log('Supplier form handler attached');
        }
        
        // Transaction form submission
        const transactionForm = document.getElementById('transaction-form');
        if (transactionForm) {
            transactionForm.addEventListener('submit', function(e) {
                e.preventDefault();
                saveTransaction();
            });
            console.log(' Transaction form handler attached');
        }
        
        // Business form submission
        const businessForm = document.getElementById('business-form');
        if (businessForm) {
            businessForm.addEventListener('submit', function(e) {
                e.preventDefault();
                saveBusiness(e);
            });
            console.log('Business form handler attached');
        } else {
            console.log('❌ Business form not found');
        }
        
        // Payment form submission
        const paymentForm = document.getElementById('payment-form');
        if (paymentForm) {
            paymentForm.addEventListener('submit', function(e) {
                e.preventDefault();
                savePayment();
            });
            console.log(' Payment form handler attached');
        }

        // Add click handlers for add buttons
        const addInventoryBtn = document.getElementById('add-inventory-btn');
        if (addInventoryBtn) {
            addInventoryBtn.addEventListener('click', () => {
                openModal('inventory-modal');
            });
            console.log(' Add inventory button handler attached');
        }

        const addSupplierBtn = document.getElementById('add-supplier-btn');
        if (addSupplierBtn) {
            addSupplierBtn.addEventListener('click', () => {
                openModal('supplier-modal');
            });
            console.log(' Add supplier button handler attached');
        }
        
        const addTransactionBtn = document.getElementById('add-transaction-btn');
        if (addTransactionBtn) {
            addTransactionBtn.addEventListener('click', () => {
                openModal('transaction-modal');
            });
            console.log(' Add transaction button handler attached');
        }
        
        const addBusinessBtn = document.getElementById('add-business-btn');
        if (addBusinessBtn) {
            addBusinessBtn.addEventListener('click', () => {
                openModal('business-modal');
            });
            console.log('✅ Add business button handler attached');
        }
        
        // Cancel buttons
        const cancelBusiness = document.getElementById('cancel-business');
        if (cancelBusiness) {
            cancelBusiness.addEventListener('click', () => {
                closeModal('business-modal');
            });
        }
    }

    // Close modal when clicking X (works on all pages)
    document.querySelectorAll('.close, .modal-close, .btn-cancel').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const modal = this.closest('.modal');
            if (modal) modal.classList.remove('active');
        });
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('active');
        }
    });
});

// Edit functions
window.editTransaction = function(id) {
    showToast('Edit feature coming soon', 'info');
};

window.editInventoryItem = function(id) {
    showToast('Edit feature coming soon', 'info');
};

window.editSupplier = function(id) {
    showToast('Edit feature coming soon', 'info');
};

// Delete functions
window.deleteTransaction = async function(id) {
    if (!confirm('Delete this transaction?')) return;
    
    const response = await fetch(`${API_BASE}/transactions/${id}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
    });
    
    if (response.ok) {
        showToast('Transaction deleted', 'success');
        loadRecentTransactions();
        loadSummaryData();
        loadCharts();
    } else {
        showToast('Failed to delete transaction', 'error');
    }
};

window.deleteInventoryItem = async function(id) {
    if (!confirm('Delete this item?')) return;
    
    const response = await fetch(`${API_BASE}/inventory/${id}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
    });
    
    if (response.ok) {
        showToast('Item deleted', 'success');
        loadInventoryAlerts();

    } else {
        showToast('Failed to delete item', 'error');
    }
};

window.deleteSupplier = async function(id) {
    if (!confirm('Delete this supplier?')) return;
    
    const response = await fetch(`${API_BASE}/suppliers/${id}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
    });
    
    if (response.ok) {
        showToast('Supplier deleted', 'success');
        window.location.reload();
    } else {
        showToast('Failed to delete supplier', 'error');
    }
};

// Other utility functions
window.restockInventoryItem = function(id) {
    showToast('Restock feature coming soon', 'info');
};

window.viewSupplierPayments = function(supplierId) {
    showToast('View payments feature coming soon', 'info');
};

window.showAddPaymentModal = function(supplierId, supplierName) {
    document.getElementById('payment-supplier').value = supplierName;
    document.getElementById('payment-amount').value = '';
    document.getElementById('payment-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('payment-notes').value = '';
    
    // Store supplier ID for save operation
    document.getElementById('payment-modal').dataset.supplierId = supplierId;
    openModal('payment-modal');
};

window.showAddCategoryModal = function() {
    showToast('Add category feature coming soon', 'info');
};

// Logout function
function logout() {
    localStorage.clear();
    showToast('Logged out successfully', 'success');
    setTimeout(() => {
        window.location.href = '/index.html';
    }, 1000);
}

// Make functions available globally
window.saveInventoryItem = saveInventoryItem;
window.saveSupplier = saveSupplier;
window.saveTransaction = saveTransaction;
window.saveBusiness = saveBusiness;
window.savePayment = savePayment;
window.openModal = openModal;
window.closeModal = closeModal;
window.logout = logout;
window.loadDashboardData = loadDashboardData;
window.loadBusinesses = loadBusinesses;

console.log('All SmartPesa functions loaded');

