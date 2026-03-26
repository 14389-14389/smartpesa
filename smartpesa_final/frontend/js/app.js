// ============================================
// SmartPesa Main Application – Final Edition
// ============================================

// State
let currentUser = null;
let currentBusinessId = null;
let businesses = [];
let inventoryItems = [];
let suppliers = [];
let transactions = [];
let posCart = [];
let lastSale = null;

// DOM Elements
const screens = {
    login: document.getElementById('login-screen'),
    register: document.getElementById('register-screen'),
    dashboard: document.getElementById('dashboard-screen')
};

const views = {
    dashboard: document.getElementById('dashboard-view'),
    transactions: document.getElementById('transactions-view'),
    forecast: document.getElementById('forecast-view'),
    inventory: document.getElementById('inventory-view'),
    suppliers: document.getElementById('suppliers-view'),
    businesses: document.getElementById('businesses-view'),
    risk: document.getElementById('risk-view'),
    pos: document.getElementById('pos-view'),
    profit: document.getElementById('profit-view'),
    employees: document.getElementById('employees-view'),
    expenses: document.getElementById('expenses-view')
};

const navItems = document.querySelectorAll('.nav-item');
const pageTitle = document.getElementById('page-title');
const businessSelect = document.getElementById('business-select');
const userNameSpan = document.getElementById('user-name');
const userEmailSpan = document.getElementById('user-email');
const logoutBtn = document.getElementById('logout-btn');

// Modals
const inventoryModal = document.getElementById('inventory-modal');
const stockModal = document.getElementById('stock-modal');
const supplierModal = document.getElementById('supplier-modal');
const paymentModal = document.getElementById('payment-modal');
const addStockModal = document.getElementById('add-stock-modal');
const receiptModal = document.getElementById('receipt-modal');
const rankModal = document.getElementById('rank-modal');
const employeeModal = document.getElementById('employee-modal');
const salaryModal = document.getElementById('salary-modal');
const expenseModal = document.getElementById('expense-modal');
const businessModal = document.getElementById('business-modal');
const editRankModal = document.getElementById('edit-rank-modal');
const editEmployeeModal = document.getElementById('edit-employee-modal');

// Charts
let cashflowChart, categoryChart, profitChart, forecastChart;

// Auto‑refresh timer
let refreshInterval = null;

// ============================================
// Utility Functions
// ============================================

function showMessage(message, type = 'info') {
    alert(message);
}

function formatCurrency(amount) {
    return 'KES ' + parseFloat(amount).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

function formatDate(dateString) {
    const d = new Date(dateString);
    return d.toLocaleDateString('en-KE', { year: 'numeric', month: 'short', day: 'numeric' });
}

function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function removeToken() {
    localStorage.removeItem('token');
}

function authHeader() {
    const token = getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// ============================================
// API Calls
// ============================================

async function apiRequest(endpoint, method = 'GET', data = null) {
    const url = API_BASE + endpoint;
    const headers = {
        'Content-Type': 'application/json',
        ...authHeader()
    };
    const options = { method, headers };
    if (data) options.body = JSON.stringify(data);
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            if (response.status === 401) {
                removeToken();
                stopAutoRefresh();
                showScreen('login');
                throw new Error('Session expired. Please login again.');
            }
            const errorData = await response.json().catch(() => ({}));
            console.error('API error response:', errorData);
            let errorMessage = '';
            if (errorData.detail) {
                if (Array.isArray(errorData.detail)) {
                    errorMessage = errorData.detail.map(e => e.msg || e.message || JSON.stringify(e)).join('; ');
                } else {
                    errorMessage = errorData.detail;
                }
            } else if (Array.isArray(errorData)) {
                errorMessage = errorData.map(e => e.msg || e.message || JSON.stringify(e)).join('; ');
            } else if (typeof errorData === 'object') {
                errorMessage = JSON.stringify(errorData);
            } else {
                errorMessage = errorData || `Request failed with status ${response.status}`;
            }
            throw new Error(errorMessage);
        }
        return await response.json();
    } catch (error) {
        console.error('API error:', error);
        throw error;
    }
}

// ============================================
// Authentication
// ============================================

async function login(email, password) {
    try {
        const data = await apiRequest('/users/login', 'POST', { email, password });
        setToken(data.access_token);
        await loadUserProfile();
        await loadBusinesses();
        showScreen('dashboard');
        showView('dashboard');
        startAutoRefresh();
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function register(email, password) {
    try {
        await apiRequest('/users/register', 'POST', { email, password });
        showMessage('Registration successful. Please login.', 'success');
        showScreen('login');
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function loadUserProfile() {
    try {
        const user = await apiRequest('/users/me');
        currentUser = user;
        userNameSpan.textContent = user.full_name || user.email.split('@')[0];
        userEmailSpan.textContent = user.email;
    } catch (error) {
        console.error('Failed to load user profile', error);
        throw error;
    }
}

// ============================================
// Real‑time Auto‑Refresh
// ============================================

function startAutoRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(() => {
        const activeView = document.querySelector('.view.active')?.id.replace('-view', '');
        if (activeView === 'inventory') {
            loadInventory();
        } else if (activeView === 'profit') {
            loadProfitReport();
        } else if (activeView === 'dashboard') {
            loadTransactions();
        } else if (activeView === 'pos') {
            loadPosProducts();
        } else if (activeView === 'employees') {
            loadEmployeesView();
        } else if (activeView === 'expenses') {
            loadExpensesView();
        } else if (activeView === 'suppliers') {
            loadSuppliers();
        }
        // Forecast is NOT auto-refreshed – use manual refresh or period change
    }, 100000);
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// ============================================
// Businesses
// ============================================

async function loadBusinesses() {
    try {
        businesses = await apiRequest('/businesses/');
        renderBusinessSelect();
        renderBusinessesGrid();
        // Ensure currentBusinessId is valid
        if (businesses.length > 0) {
            if (!currentBusinessId) {
                currentBusinessId = businesses[0].id;
                businessSelect.value = currentBusinessId;
            } else if (!businesses.find(b => b.id === currentBusinessId)) {
                // Current business ID is not in the list – reset to first
                currentBusinessId = businesses[0].id;
                businessSelect.value = currentBusinessId;
                console.log('Business ID reset to', currentBusinessId);
            }
        }
        if (currentBusinessId) {
            loadDashboardData();
        }
    } catch (error) {
        console.error('Failed to load businesses', error);
    }
}

function renderBusinessSelect() {
    let options = '<option value="">Select Business</option>';
    businesses.forEach(b => {
        options += `<option value="${b.id}">${b.name}</option>`;
    });
    businessSelect.innerHTML = options;
    if (currentBusinessId) businessSelect.value = currentBusinessId;
}

function renderBusinessesGrid() {
    const grid = document.getElementById('businesses-grid');
    if (!grid) return;
    if (businesses.length === 0) {
        grid.innerHTML = '<p>No businesses found. Create one first.</p>';
        return;
    }
    let html = '';
    businesses.forEach(b => {
        html += `
            <div class="business-card" onclick="selectBusiness(${b.id})">
                <h3>${b.name}</h3>
                <p>${b.type || 'Business'}</p>
                <p>${b.currency || 'KES'}</p>
                <button class="delete-btn" data-delete="business" data-id="${b.id}"><i class="fas fa-trash"></i></button>
            </div>
        `;
    });
    grid.innerHTML = html;
}

window.selectBusiness = function(id) {
    currentBusinessId = id;
    businessSelect.value = id;
    loadDashboardData();
};

window.deleteBusiness = async function(id) {
    if (!confirm('Are you sure you want to delete this business? All associated data will be lost.')) return;
    try {
        await apiRequest(`/businesses/${id}`, 'DELETE');
        await loadBusinesses();
        if (businesses.length > 0) {
            currentBusinessId = businesses[0].id;
        } else {
            currentBusinessId = null;
        }
        showMessage('Business deleted', 'success');
    } catch (error) {
        showMessage(error.message, 'error');
    }
};

async function createBusiness(name, type, currency) {
    try {
        const newBusiness = await apiRequest('/businesses/', 'POST', { name, type, currency });
        businesses.push(newBusiness);
        renderBusinessSelect();
        renderBusinessesGrid();
        if (!currentBusinessId) {
            currentBusinessId = newBusiness.id;
            businessSelect.value = currentBusinessId;
        }
        businessModal.classList.remove('active');
        showMessage('Business created', 'success');
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// ============================================
// Business Select Event Listener
// ============================================
businessSelect.addEventListener('change', (e) => {
    currentBusinessId = parseInt(e.target.value);
    console.log('Business changed to', currentBusinessId);

    const posIdField = document.getElementById('pos-business-id');
    if (posIdField) {
        posIdField.value = currentBusinessId;
        console.log('POS Business ID set to', posIdField.value);
    }

    const activeView = document.querySelector('.view.active')?.id.replace('-view', '');
    if (activeView === 'dashboard') loadDashboardData();
    if (activeView === 'transactions') loadTransactions();
    if (activeView === 'inventory') loadInventory();
    if (activeView === 'suppliers') loadSuppliers();
    if (activeView === 'pos') loadInventory();  // loadInventory will also refresh POS product list
    if (activeView === 'employees') loadEmployeesView();
    if (activeView === 'expenses') loadExpensesView();
    if (activeView === 'profit') loadProfitReport();
    if (activeView === 'forecast') loadForecast();
});

// ============================================
// Dashboard Data
// ============================================

async function loadDashboardData() {
    if (!currentBusinessId) return;
    try {
        await loadTransactions();
        updateDashboardKPIs();
        updateDashboardCharts();
        loadRecentTransactions();
    } catch (error) {
        console.error('Failed to load dashboard data', error);
    }
}

async function loadTransactions() {
    if (!currentBusinessId) return;
    try {
        transactions = await apiRequest(`/transactions/?business_id=${currentBusinessId}`);
        renderAllTransactions();
    } catch (error) {
        console.error('Failed to load transactions', error);
    }
}

function updateDashboardKPIs() {
    const now = new Date();
    const thirtyDaysAgo = new Date(now.setDate(now.getDate() - 30));
    const recent = transactions.filter(t => new Date(t.created_at) >= thirtyDaysAgo);
    const income = recent.filter(t => t.type === 'income').reduce((sum, t) => sum + t.amount, 0);
    const expense = recent.filter(t => t.type === 'expense').reduce((sum, t) => sum + t.amount, 0);
    const net = income - expense;
    document.getElementById('total-income').textContent = formatCurrency(income);
    document.getElementById('total-expense').textContent = formatCurrency(expense);
    document.getElementById('net-cashflow').textContent = formatCurrency(net);
    document.getElementById('risk-score').textContent = '68';
}

function updateDashboardCharts() {
    const labels = [];
    const incomeData = [];
    const expenseData = [];
    for (let i = 29; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const dateStr = d.toISOString().split('T')[0];
        labels.push(dateStr.slice(5));
        const dayTransactions = transactions.filter(t => t.created_at.startsWith(dateStr));
        const dayIncome = dayTransactions.filter(t => t.type === 'income').reduce((s, t) => s + t.amount, 0);
        const dayExpense = dayTransactions.filter(t => t.type === 'expense').reduce((s, t) => s + t.amount, 0);
        incomeData.push(dayIncome);
        expenseData.push(dayExpense);
    }

    if (cashflowChart) cashflowChart.destroy();
    const ctx1 = document.getElementById('cashflow-chart').getContext('2d');
    cashflowChart = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                { label: 'Income', data: incomeData, borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.1)', tension: 0.4 },
                { label: 'Expense', data: expenseData, borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.1)', tension: 0.4 }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });

    const categories = {};
    transactions.forEach(t => {
        if (!categories[t.category]) categories[t.category] = 0;
        categories[t.category] += t.amount;
    });
    const catLabels = Object.keys(categories);
    const catData = Object.values(categories);
    if (categoryChart) categoryChart.destroy();
    const ctx2 = document.getElementById('category-chart').getContext('2d');
    categoryChart = new Chart(ctx2, {
        type: 'doughnut',
        data: {
            labels: catLabels,
            datasets: [{ data: catData, backgroundColor: ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6'] }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

function loadRecentTransactions() {
    const tbody = document.getElementById('recent-transactions-body');
    const recent = transactions.slice(0, 5);
    if (recent.length === 0) {
        tbody.innerHTML = '<td colspan="5">No transactions found<\/td>';
        return;
    }
    let html = '';
    recent.forEach(t => {
        html += `
            <tr>
                <td>${formatDate(t.created_at)}电子
                <td>${t.description || '-'}电子
                <td>${t.category || '-'}电子
                <td>${formatCurrency(t.amount)}电子
                <td><span class="badge ${t.type}">${t.type}</span>电子
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function renderAllTransactions() {
    const tbody = document.getElementById('transactions-body');
    if (!tbody) return;
    if (transactions.length === 0) {
        tbody.innerHTML = '<td colspan="5">No transactions<\/td>';
        return;
    }
    let html = '';
    transactions.forEach(t => {
        html += `
            <tr>
                <td>${formatDate(t.created_at)}电子
                <td>${t.description || '-'}电子
                <td>${t.category || '-'}电子
                <td>${formatCurrency(t.amount)}电子
                <td><span class="badge ${t.type}">${t.type}</span>电子
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

// ============================================
// Inventory
// ============================================

async function loadInventory() {
    if (!currentBusinessId) return;
    try {
        inventoryItems = await apiRequest(`/inventory/?business_id=${currentBusinessId}`);
        renderInventoryTable();
        updateInventoryStats();
        loadLowStockAlerts();

        // If POS view is active, refresh the product list
        const posView = document.getElementById('pos-view');
        if (posView && posView.classList.contains('active')) {
            loadPosProducts();
        }
    } catch (error) {
        console.error('Failed to load inventory', error);
    }
}

function renderInventoryTable() {
    const tbody = document.getElementById('inventory-table-body');
    if (!tbody) return;
    if (inventoryItems.length === 0) {
        tbody.innerHTML = '<td colspan="8">No inventory items<\/td>';
        return;
    }
    let html = '';
    inventoryItems.forEach(item => {
        const totalValue = item.quantity * item.price_per_unit;
        let statusClass = 'normal-stock';
        if (item.quantity <= item.reorder_level) statusClass = 'low-stock';
        else if (item.quantity <= item.reorder_level * 2) statusClass = 'medium-stock';
        html += `
            <tr>
                <td>${item.sku || '-'}电子
                <td>${item.name}电子
                <td>${item.quantity}电子
                <td>${item.unit}电子
                <td>${formatCurrency(item.price_per_unit)}电子
                <td>${formatCurrency(totalValue)}电子
                <td><span class="badge ${statusClass}">${statusClass.replace('-',' ')}</span>电子
                <td class="action-buttons">
                    <button onclick="adjustStock(${item.id}, '${item.name}')" title="Adjust Stock"><i class="fas fa-edit"></i></button>
                    <button data-delete="inventory" data-id="${item.id}" title="Delete"><i class="fas fa-trash"></i></button>
                电子
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function updateInventoryStats() {
    const totalItems = inventoryItems.length;
    const lowStock = inventoryItems.filter(i => i.quantity <= i.reorder_level).length;
    const totalValue = inventoryItems.reduce((sum, i) => sum + i.quantity * i.price_per_unit, 0);
    document.getElementById('total-items').textContent = totalItems;
    document.getElementById('low-stock-count').textContent = lowStock;
    document.getElementById('inventory-value').textContent = formatCurrency(totalValue);
    document.getElementById('turnover-rate').textContent = '15%';
}

async function addInventoryItem(item) {
    try {
        const newItem = await apiRequest('/inventory/', 'POST', { business_id: currentBusinessId, ...item });
        const purchaseCost = parseFloat(document.getElementById('inv-purchase-cost').value);
        const purchaseDate = document.getElementById('inv-purchase-date').value;
        await apiRequest('/purchases/', 'POST', {
            product_id: newItem.id,
            quantity: item.quantity,
            cost_per_unit: purchaseCost,
            purchase_date: purchaseDate,
            remaining_quantity: item.quantity,
            supplier_id: null,
            notes: "Initial stock from inventory addition"
        });
        inventoryItems.push(newItem);
        renderInventoryTable();
        updateInventoryStats();
        inventoryModal.classList.remove('active');
        showMessage('Item added with purchase batch', 'success');
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function deleteInventoryItem(id) {
    if (!confirm('Are you sure?')) return;
    try {
        await apiRequest(`/inventory/${id}`, 'DELETE');
        inventoryItems = inventoryItems.filter(i => i.id !== id);
        renderInventoryTable();
        updateInventoryStats();
        showMessage('Item deleted', 'success');
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// ============================================
// Stock Adjustment
// ============================================
async function adjustStock(id, name) {
    document.getElementById('stock-item-id').value = id;
    document.getElementById('stock-item-name').textContent = name;
    document.getElementById('stock-adj-quantity').value = '';
    document.getElementById('stock-notes').value = '';
    stockModal.classList.add('active');
}

document.getElementById('stock-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('stock-item-id').value;
    const quantity = parseFloat(document.getElementById('stock-adj-quantity').value);
    const type = document.getElementById('stock-type').value;
    const notes = document.getElementById('stock-notes').value;
    if (isNaN(quantity) || quantity <= 0) {
        showMessage('Invalid quantity', 'error');
        return;
    }
    try {
        const item = inventoryItems.find(i => i.id == id);
        if (!item) return;
        const change = type === 'add' ? quantity : -quantity;
        const updated = await apiRequest(`/inventory/${id}`, 'PUT', {
            ...item,
            quantity: item.quantity + change
        });
        Object.assign(item, updated);
        renderInventoryTable();
        updateInventoryStats();
        stockModal.classList.remove('active');
        showMessage('Stock updated', 'success');
    } catch (error) {
        showMessage(error.message, 'error');
    }
});

async function loadLowStockAlerts() {
    try {
        const alerts = await apiRequest(`/inventory/alerts/low-stock?business_id=${currentBusinessId}`);
        const container = document.getElementById('low-stock-alerts');
        if (!container) return;
        if (alerts.length === 0) {
            container.innerHTML = '';
            return;
        }
        let html = '<h4>Low Stock Alerts</h4>';
        alerts.forEach(a => {
            html += `<div class="alert-item high"><i class="fas fa-exclamation-triangle"></i> ${a.name} (${a.current_quantity} left, reorder at ${a.reorder_level})</div>`;
        });
        container.innerHTML = html;
    } catch (error) {
        console.error('Failed to load low stock alerts', error);
    }
}

// ============================================
// Suppliers
// ============================================

async function loadRecentPayments() {
    if (!currentBusinessId) return;
    try {
        const payments = await apiRequest(`/suppliers/payments/all?business_id=${currentBusinessId}&limit=10`);
        const tbody = document.getElementById('payments-table-body');
        if (!tbody) return;
        if (payments.length === 0) {
            tbody.innerHTML = '<td colspan="4">No payments recorded<\/td>';
            return;
        }
        let html = '';
        payments.forEach(p => {
            html += `
                <tr>
                    <td>${formatDate(p.due_date)}电子
                    <td>${p.supplier_name}电子
                    <td>${formatCurrency(p.amount)}电子
                    <td>${p.notes || '-'}电子
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (error) {
        console.error('Failed to load recent payments', error);
    }
}

async function loadSuppliers() {
    if (!currentBusinessId) return;
    try {
        suppliers = await apiRequest(`/suppliers/?business_id=${currentBusinessId}`);
        renderSuppliersGrid();
        updateSupplierStats();
        loadRecentPayments();   // Load recent payments table
    } catch (error) {
        console.error('Failed to load suppliers', error);
    }
}

function renderSuppliersGrid() {
    const grid = document.getElementById('suppliers-grid');
    if (!grid) return;
    if (suppliers.length === 0) {
        grid.innerHTML = '<p>No suppliers yet. Add one.</p>';
        return;
    }
    let html = '';
    suppliers.forEach(s => {
        html += `
            <div class="supplier-card">
                <div class="supplier-header">
                    <h3>${s.name}</h3>
                    <span class="badge ${s.is_active ? 'paid' : 'inactive'}">${s.is_active ? 'Active' : 'Inactive'}</span>
                </div>
                <div class="supplier-contact"><i class="fas fa-user"></i> ${s.contact_person || '-'}</div>
                <div class="supplier-contact"><i class="fas fa-phone"></i> ${s.phone || '-'}</div>
                <div class="supplier-contact"><i class="fas fa-envelope"></i> ${s.email || '-'}</div>
                <div class="supplier-footer">
                    <span class="payment-badge pending">Terms: ${s.payment_terms}</span>
                    <button onclick="recordPayment(${s.id}, '${s.name}')" class="btn-icon"><i class="fas fa-money-bill"></i></button>
                </div>
            </div>
        `;
    });
    grid.innerHTML = html;
}

function updateSupplierStats() {
    document.getElementById('total-suppliers').textContent = suppliers.length;
    document.getElementById('total-outstanding').textContent = formatCurrency(0);
    document.getElementById('total-overdue').textContent = formatCurrency(0);
    document.getElementById('pending-count').textContent = '0';
}

async function addSupplier(supplier) {
    try {
        const newSup = await apiRequest('/suppliers/', 'POST', { business_id: currentBusinessId, ...supplier });
        suppliers.push(newSup);
        renderSuppliersGrid();
        updateSupplierStats();
        supplierModal.classList.remove('active');
        showMessage('Supplier added', 'success');
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function recordPayment(id, name) {
    document.getElementById('payment-supplier-id').value = id;
    document.getElementById('payment-supplier-name').textContent = name;
    document.getElementById('payment-amount').value = '';
    document.getElementById('payment-due-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('payment-notes').value = '';
    paymentModal.classList.add('active');
}

// ============================================
// Employees
// ============================================

async function loadEmployeesView() {
    await loadRanks();
    await loadEmployees();
    await loadSalaryPayments();
}

async function loadRanks() {
    try {
        const ranks = await apiRequest('/employees/ranks');
        const tbody = document.getElementById('ranks-table-body');
        if (!tbody) return;
        tbody.innerHTML = ranks.map(r => `
             <tr>
                <td>${r.id}电子
                <td>${r.name}电子
                <td>${formatCurrency(r.base_salary)}电子
                <td>${r.description || ''}电子
                <td class="action-buttons">
                    <button class="btn-icon" onclick="editRank(${r.id})"><i class="fas fa-edit"></i></button>
                    <button class="btn-icon" data-delete="rank" data-id="${r.id}"><i class="fas fa-trash"></i></button>
                电子
             </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load ranks:', error);
    }
}

async function loadEmployees() {
    try {
        const employees = await apiRequest('/employees/?active_only=false');
        const tbody = document.getElementById('employees-table-body');
        if (!tbody) return;
        tbody.innerHTML = employees.map(e => `
             <tr>
                <td>${e.id}电子
                <td>${e.name}电子
                <td>${e.rank?.name || ''}电子
                <td>${formatCurrency(e.monthly_salary)}电子
                <td>${e.hire_date}电子
                <td><span class="badge ${e.is_active ? 'paid' : 'pending'}">${e.is_active ? 'Active' : 'Inactive'}</span>电子
                <td class="action-buttons">
                    <button class="btn-icon" onclick="editEmployee(${e.id})"><i class="fas fa-edit"></i></button>
                    <button class="btn-icon" onclick="fireEmployee(${e.id})"><i class="fas fa-user-minus"></i></button>
                    <button class="btn-icon delete" data-delete="employee" data-id="${e.id}"><i class="fas fa-trash"></i></button>
                电子
             </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load employees:', error);
    }
}

async function loadSalaryPayments() {
    try {
        const payments = await apiRequest('/salary-payments/');
        const tbody = document.getElementById('salary-payments-table-body');
        if (!tbody) return;
        tbody.innerHTML = payments.map(p => `
             <tr>
                <td>${p.id}电子
                <td>${p.employee?.name || ''}电子
                <td>${formatCurrency(p.amount)}电子
                <td>${p.payment_date}电子
                <td>${p.month}电子
             </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load salary payments:', error);
    }
}

async function deleteRank(id) {
    if (!confirm('Delete this rank? All employees with this rank will be affected.')) return;
    try {
        await apiRequest(`/employees/ranks/${id}`, 'DELETE');
        loadRanks();
        loadEmployees(); // ranks might affect employees
    } catch (error) {
        alert('Failed to delete rank: ' + error.message);
    }
}

async function fireEmployee(id) {
    if (!confirm('Fire this employee? They will be marked as inactive.')) return;
    try {
        await apiRequest(`/employees/${id}`, 'PUT', {
            is_active: false,
            termination_date: new Date().toISOString().split('T')[0]
        });
        loadEmployees();
        await loadTransactions();
        refreshProfitIfVisible();
    } catch (error) {
        alert('Failed to fire employee: ' + error.message);
    }
}

async function deleteEmployee(id) {
    if (!confirm('Permanently delete this employee? This action cannot be undone.')) return;
    try {
        await apiRequest(`/employees/${id}`, 'DELETE');
        loadEmployees();
        await loadTransactions();
        refreshProfitIfVisible();
    } catch (error) {
        alert('Failed to delete employee: ' + error.message);
    }
}

// Edit rank functions
async function editRank(id) {
    try {
        const ranks = await apiRequest('/employees/ranks');
        const rank = ranks.find(r => r.id === id);
        if (!rank) throw new Error('Rank not found');
        document.getElementById('edit-rank-id').value = rank.id;
        document.getElementById('edit-rank-name').value = rank.name;
        document.getElementById('edit-rank-base-salary').value = rank.base_salary;
        document.getElementById('edit-rank-description').value = rank.description || '';
        editRankModal.classList.add('active');
    } catch (error) {
        alert('Failed to load rank details: ' + error.message);
    }
}

async function updateRank() {
    const id = document.getElementById('edit-rank-id').value;
    const data = {
        name: document.getElementById('edit-rank-name').value,
        base_salary: parseFloat(document.getElementById('edit-rank-base-salary').value),
        description: document.getElementById('edit-rank-description').value
    };
    try {
        await apiRequest(`/employees/ranks/${id}`, 'PUT', data);
        editRankModal.classList.remove('active');
        loadRanks();
        loadEmployees(); // in case employee ranks changed
        showMessage('Rank updated', 'success');
    } catch (error) {
        alert('Failed to update rank: ' + error.message);
    }
}

// Edit employee functions
async function editEmployee(id) {
    try {
        const employees = await apiRequest('/employees/?active_only=false');
        const employee = employees.find(e => e.id === id);
        if (!employee) throw new Error('Employee not found');
        const ranks = await apiRequest('/employees/ranks');
        document.getElementById('edit-employee-id').value = employee.id;
        document.getElementById('edit-employee-name').value = employee.name;
        document.getElementById('edit-employee-rank').innerHTML = ranks.map(r => `<option value="${r.id}" ${r.id === employee.rank_id ? 'selected' : ''}>${r.name}</option>`).join('');
        document.getElementById('edit-employee-salary').value = employee.monthly_salary;
        document.getElementById('edit-employee-phone').value = employee.phone || '';
        document.getElementById('edit-employee-email').value = employee.email || '';
        document.getElementById('edit-employee-hire-date').value = employee.hire_date;
        document.getElementById('edit-employee-active').checked = employee.is_active;
        editEmployeeModal.classList.add('active');
    } catch (error) {
        alert('Failed to load employee details: ' + error.message);
    }
}

async function updateEmployee() {
    const id = document.getElementById('edit-employee-id').value;
    const data = {
        name: document.getElementById('edit-employee-name').value,
        rank_id: parseInt(document.getElementById('edit-employee-rank').value),
        monthly_salary: parseFloat(document.getElementById('edit-employee-salary').value),
        phone: document.getElementById('edit-employee-phone').value,
        email: document.getElementById('edit-employee-email').value,
        hire_date: document.getElementById('edit-employee-hire-date').value,
        is_active: document.getElementById('edit-employee-active').checked
    };
    try {
        await apiRequest(`/employees/${id}`, 'PUT', data);
        editEmployeeModal.classList.remove('active');
        loadEmployees();
        await loadTransactions();
        refreshProfitIfVisible();
        showMessage('Employee updated', 'success');
    } catch (error) {
        alert('Failed to update employee: ' + error.message);
    }
}

// ============================================
// Expenses
// ============================================

async function loadExpensesView() {
    await loadExpenseCategories();
    await loadExpenses();
}

async function loadExpenseCategories() {
    try {
        const cats = await apiRequest('/expenses/categories');
        const tbody = document.getElementById('categories-table-body');
        if (!tbody) return;
        tbody.innerHTML = cats.map(c => `
             <tr>
                <td>${c.id}电子
                <td>${c.name}电子
                <td>${c.description || ''}电子
             </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

async function loadExpenses() {
    try {
        const expenses = await apiRequest('/expenses/');
        const tbody = document.getElementById('expenses-table-body');
        if (!tbody) return;
        tbody.innerHTML = expenses.map(e => `
             <tr>
                <td>${e.id}电子
                <td>${e.expense_date}电子
                <td>${e.category?.name || ''}电子
                <td>${formatCurrency(e.amount)}电子
                <td>${e.description || ''}电子
                <td>${e.receipt_image ? '<a href="#" onclick="viewReceipt(\''+e.receipt_image+'\')">View</a>' : ''}电子
             </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load expenses:', error);
    }
}

// ============================================
// POS Functions
// ============================================

function renderProductCheckboxes() {
    const container = document.getElementById('product-list');
    if (!container) return;
    container.innerHTML = '';
    inventoryItems.forEach(p => {
        const div = document.createElement('div');
        div.className = 'product-item';
        div.innerHTML = `
            <input type="checkbox" class="product-checkbox" data-id="${p.id}" data-name="${p.name}" data-price="${p.price_per_unit}" data-stock="${p.quantity}">
            <span class="product-info">${p.id} - ${p.name}</span>
            <span class="product-stock">Stock: ${p.quantity}</span>
            <span class="product-price">${formatCurrency(p.price_per_unit)}</span>
            <input type="number" class="product-qty" data-id="${p.id}" min="1" max="${p.quantity}" value="1" style="width:70px;">
        `;
        container.appendChild(div);
    });
}

document.getElementById('pos-add-selected').addEventListener('click', () => {
    const checkboxes = document.querySelectorAll('.product-checkbox:checked');
    if (checkboxes.length === 0) {
        alert('Select at least one product');
        return;
    }
    checkboxes.forEach(cb => {
        const id = parseInt(cb.dataset.id);
        const name = cb.dataset.name;
        const price = parseFloat(cb.dataset.price);
        const maxStock = parseInt(cb.dataset.stock);
        const qtyInput = document.querySelector(`.product-qty[data-id="${id}"]`);
        const qty = qtyInput ? parseInt(qtyInput.value) : 1;
        if (qty < 1 || qty > maxStock) {
            alert(`Invalid quantity for ${name} (max ${maxStock})`);
            return;
        }
        const existing = posCart.find(item => item.product_id === id);
        if (existing) {
            if (existing.quantity + qty > maxStock) {
                alert(`Cannot add more ${name} – only ${maxStock - existing.quantity} left`);
                return;
            }
            existing.quantity += qty;
        } else {
            posCart.push({
                product_id: id,
                name: name,
                quantity: qty,
                unit_price: price
            });
        }
    });
    renderPosCart();
    checkboxes.forEach(cb => cb.checked = false);
});

function loadPosProducts() {
    renderProductCheckboxes();
    const businessIdInput = document.getElementById('pos-business-id');
    if (businessIdInput) {
        businessIdInput.value = currentBusinessId;
    }
}

function renderPosCart() {
    const tbody = document.getElementById('pos-cart-body');
    if (!tbody) return;
    let html = '';
    let total = 0;
    posCart.forEach((item, idx) => {
        const subtotal = item.quantity * item.unit_price;
        total += subtotal;
        html += `
             <tr>
                <td>${item.name}电子
                <td>${item.unit_price}电子
                <td>${item.quantity}电子
                <td>${subtotal.toFixed(2)}电子
                <td><button onclick="removeFromPosCart(${idx})">❌</button>电子
             </tr>
        `;
    });
    tbody.innerHTML = html;
    document.getElementById('pos-total').textContent = total.toFixed(2);
}

window.removeFromPosCart = (idx) => {
    posCart.splice(idx, 1);
    renderPosCart();
};

document.getElementById('pos-complete-sale').addEventListener('click', async () => {
    if (posCart.length === 0) return alert('Cart empty');
    const saleData = {
        business_id: parseInt(document.getElementById('pos-business-id').value),
        payment_method: document.getElementById('pos-payment-method').value,
        customer_name: document.getElementById('pos-customer-name').value || null,
        items: posCart.map(item => ({
            product_id: item.product_id,
            quantity: item.quantity,
            unit_price: item.unit_price,
            discount: 0
        }))
    };
    try {
        const sale = await apiRequest('/sales/', 'POST', saleData);
        lastSale = sale;
        showMessage('Sale completed', 'success');
        posCart = [];
        renderPosCart();
        loadPosProducts();
        loadInventory();
        await loadTransactions();
        refreshProfitIfVisible();
        showReceipt(sale);
    } catch (err) {
        showMessage(err.message, 'error');
    }
});

function showReceipt(sale) {
    const container = document.getElementById('receipt-details');
    const date = new Date(sale.sale_date).toLocaleString();
    let totalRevenue = 0;
    let totalCost = 0;
    let itemsHtml = '';
    sale.items.forEach(item => {
        const subtotal = item.quantity * item.unit_price;
        totalRevenue += subtotal;
        totalCost += item.cost_of_goods_sold;
        itemsHtml += `
             <tr>
                <td>${item.product_id}电子
                <td>${item.quantity}电子
                <td>${formatCurrency(item.unit_price)}电子
                <td>${formatCurrency(subtotal)}电子
             </tr>
        `;
    });
    const profit = totalRevenue - totalCost;
    container.innerHTML = `
        <p><strong>Sale ID:</strong> ${sale.id}</p>
        <p><strong>Date:</strong> ${date}</p>
        <p><strong>Customer:</strong> ${sale.customer_name || 'Walk-in'}</p>
        <p><strong>Payment:</strong> ${sale.payment_method}</p>
        <hr>
        <table style="width:100%; border-collapse: collapse;">
            <thead> 氧化钙<th>Item</th><th>Qty</th><th>Price</th><th>Subtotal</th> </thead>
            <tbody>${itemsHtml}</tbody>
            <tfoot>
                 <td colspan="3" style="text-align:right;"><strong>Total:</strong> <strong>${formatCurrency(totalRevenue)}</strong> 电子
                 <td colspan="3" style="text-align:right;"><strong>Profit:</strong> <strong>${formatCurrency(profit)}</strong> 电子
            </tfoot>
         </table>
    `;
    receiptModal.classList.add('active');
}

document.getElementById('print-receipt').addEventListener('click', () => {
    const printContent = document.getElementById('receipt-details').innerHTML;
    const originalTitle = document.title;
    document.title = 'SmartPesa Receipt';
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
        <head><title>Receipt</title>
        <style>
            body { font-family: monospace; padding: 20px; }
            table { width: 100%; border-collapse: collapse; }
            td, th { padding: 5px; text-align: left; }
        </style>
        </head>
        <body>${printContent}</body>
        </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
    printWindow.close();
    document.title = originalTitle;
});

document.getElementById('close-receipt').addEventListener('click', () => {
    receiptModal.classList.remove('active');
});

document.getElementById('pos-add-stock-btn').addEventListener('click', () => {
    const select = document.getElementById('stock-product');
    select.innerHTML = '<option value="">Select product</option>';
    inventoryItems.forEach(p => {
        select.innerHTML += `<option value="${p.id}">${p.id} - ${p.name}</option>`;
    });
    document.getElementById('stock-quantity').value = '';
    document.getElementById('stock-cost').value = '';
    document.getElementById('stock-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('stock-supplier').value = '';
    document.getElementById('stock-notes').value = '';
    addStockModal.classList.add('active');
});

window.openAddStockModal = function() {
    const select = document.getElementById('stock-product');
    if (!select) {
        alert('Modal elements not found. Please ensure you are on the POS view.');
        return;
    }
    select.innerHTML = '<option value="">Select product</option>';
    inventoryItems.forEach(p => {
        select.innerHTML += `<option value="${p.id}">${p.id} - ${p.name}</option>`;
    });
    document.getElementById('stock-quantity').value = '';
    document.getElementById('stock-cost').value = '';
    document.getElementById('stock-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('stock-supplier').value = '';
    document.getElementById('stock-notes').value = '';
    addStockModal.classList.add('active');
};

document.getElementById('add-stock-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const productId = document.getElementById('stock-product').value;
    const quantityRaw = document.getElementById('stock-quantity').value;
    const costRaw = document.getElementById('stock-cost').value;
    const purchaseDate = document.getElementById('stock-date').value;
    const supplierId = document.getElementById('stock-supplier').value || null;
    const notes = document.getElementById('stock-notes').value || null;

    const quantity = parseInt(quantityRaw);
    const cost = parseFloat(costRaw);

    if (!productId || isNaN(quantity) || quantity < 1 || isNaN(cost) || cost < 0) {
        showMessage('Please fill all fields correctly (quantity must be a number >0, cost must be a number >=0)', 'error');
        return;
    }

    const payload = {
        product_id: parseInt(productId),
        quantity: quantity,
        cost_per_unit: cost,
        purchase_date: purchaseDate,
        remaining_quantity: quantity,
        supplier_id: supplierId ? parseInt(supplierId) : null,
        notes: notes || "Stock added from POS"
    };

    try {
        await apiRequest('/purchases/', 'POST', payload);
        showMessage('Stock added successfully', 'success');
        addStockModal.classList.remove('active');
        loadPosProducts();
        loadInventory();
    } catch (err) {
        showMessage(err.message, 'error');
    }
});

// ============================================
// Profit Report
// ============================================

async function loadProfitReport() {
    const start = document.getElementById('profit-start').value;
    const end = document.getElementById('profit-end').value;
    if (!start || !end) return;

    if (!transactions.length && currentBusinessId) {
        await loadTransactions();
    }

    const startDate = new Date(start);
    const endDate = new Date(end);
    endDate.setHours(23, 59, 59);

    const filtered = transactions.filter(t => {
        const tDate = new Date(t.created_at);
        return tDate >= startDate && tDate <= endDate && t.business_id === currentBusinessId;
    });

    const revenue = filtered.filter(t => t.type === 'income').reduce((sum, t) => sum + t.amount, 0);
    const expenses = filtered.filter(t => t.type === 'expense').reduce((sum, t) => sum + t.amount, 0);
    const gross = revenue - expenses;
    const net = gross;

    document.getElementById('profit-revenue').textContent = formatCurrency(revenue);
    document.getElementById('profit-cogs').textContent = formatCurrency(expenses);
    document.getElementById('profit-gross').textContent = formatCurrency(gross);
    document.getElementById('profit-net').textContent = formatCurrency(net);

    if (profitChart) profitChart.destroy();
    const ctx = document.getElementById('profit-chart').getContext('2d');
    profitChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Revenue', 'Total Expenses', 'Gross Profit', 'Net Profit'],
            datasets: [{
                label: 'KES',
                data: [revenue, expenses, gross, net],
                backgroundColor: ['#2ecc71', '#e74c3c', '#3498db', '#9b59b6']
            }]
        },
        options: { responsive: true }
    });
}

function refreshProfitIfVisible() {
    const profitView = document.getElementById('profit-view');
    if (profitView && profitView.classList.contains('active')) {
        loadProfitReport();
    }
}

document.getElementById('profit-load').addEventListener('click', loadProfitReport);

// ============================================
// Forecast
// ============================================

let currentForecastPeriod = 30; // default to 30 days

async function loadForecast() {
    const container = document.getElementById('forecast-content');
    if (!container) return;

    if (!currentBusinessId) {
        container.innerHTML = '<p>Please select a business first.</p>';
        return;
    }

    // Show loading state
    container.innerHTML = '<p>Loading forecast...</p>';

    try {
        // Use the generic endpoint with the selected days
        const response = await apiRequest(`/forecast/${currentBusinessId}?days=${currentForecastPeriod}`);
        if (response.error) {
            container.innerHTML = `<p>Error: ${response.error}</p>`;
            return;
        }
        renderForecast(response);
    } catch (error) {
        console.error('Failed to load forecast:', error);
        container.innerHTML = '<p>Could not load forecast. Check console for details.</p>';
        showMessage('Could not load forecast', 'error');
    }
}

function renderForecast(data) {
    const container = document.getElementById('forecast-content');
    if (!container) return;
    container.innerHTML = '';

    // Create title with period
    const periodText = {
        7: '7‑Day (Weekly)',
        30: '30‑Day (Monthly)',
        90: '90‑Day (Quarterly)',
        365: '365‑Day (Yearly)'
    }[currentForecastPeriod] || `${currentForecastPeriod}‑Day`;
    const title = document.createElement('h3');
    title.textContent = `${periodText} Cash Flow Forecast`;
    container.appendChild(title);

    // Create canvas for chart
    const canvas = document.createElement('canvas');
    canvas.id = 'forecast-chart';
    canvas.style.maxHeight = '400px';
    container.appendChild(canvas);

    // Extract forecast data
    const dates = data.hybrid_model.forecast.map(f => new Date(f.date).toLocaleDateString());
    const prophetPreds = data.hybrid_model.forecast.map(f => f.prophet_prediction);
    const hybridPreds = data.hybrid_model.forecast.map(f => f.hybrid_prediction);

    const ctx = canvas.getContext('2d');
    if (window.forecastChart) window.forecastChart.destroy();
    window.forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Prophet Forecast',
                    data: prophetPreds,
                    borderColor: '#f59e0b',
                    backgroundColor: 'transparent',
                    tension: 0.4
                },
                {
                    label: 'Hybrid Forecast (Prophet + RF)',
                    data: hybridPreds,
                    borderColor: '#10b981',
                    backgroundColor: 'transparent',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.dataset.label}: KES ${context.raw.toFixed(2)}`
                    }
                }
            },
            scales: {
                y: {
                    title: { display: true, text: 'Cash Flow (KES)' }
                }
            }
        }
    });

    // Risk summary
    const riskDiv = document.createElement('div');
    riskDiv.className = 'risk-summary';
    riskDiv.style.marginTop = '20px';
    riskDiv.style.padding = '15px';
    riskDiv.style.backgroundColor = '#f9fafb';
    riskDiv.style.borderRadius = '8px';
    riskDiv.innerHTML = `
        <h4>Risk Analysis</h4>
        <p><strong>Risk Score:</strong> ${data.risk_analysis.risk_score} / 100</p>
        <p><strong>Negative Days Forecast:</strong> ${data.risk_analysis.negative_days_forecast}</p>
        <p><strong>Forecast Volatility:</strong> KES ${data.risk_analysis.forecast_volatility.toFixed(2)}</p>
        <p><strong>Historical Volatility:</strong> KES ${data.risk_analysis.historical_volatility.toFixed(2)}</p>
        <ul>
            ${data.risk_analysis.alerts.map(a => `<li class="alert-${a.level.toLowerCase()}">${a.message}</li>`).join('')}
        </ul>
    `;
    container.appendChild(riskDiv);
}

function initForecastControls() {
    const periodSelect = document.getElementById('forecast-period');
    const refreshBtn = document.getElementById('refresh-forecast-btn');
    if (periodSelect) {
        periodSelect.addEventListener('change', () => {
            currentForecastPeriod = parseInt(periodSelect.value);
            loadForecast();
        });
    }
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => loadForecast());
    }
}

// ============================================
// Navigation & Screen Switching
// ============================================

function showScreen(screenName) {
    Object.values(screens).forEach(s => s.classList.remove('active'));
    screens[screenName].classList.add('active');
}

function showView(viewName) {
    Object.values(views).forEach(v => { if (v) v.classList.remove('active'); });
    if (views[viewName]) views[viewName].classList.add('active');
    navItems.forEach(item => {
        if (item.dataset.view === viewName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    const titles = {
        dashboard: 'Dashboard',
        transactions: 'Transactions',
        forecast: 'Forecast',
        inventory: 'Inventory',
        suppliers: 'Suppliers',
        businesses: 'Businesses',
        risk: 'Risk Analysis',
        pos: 'Point of Sale',
        profit: 'Profit Dashboard',
        employees: 'Employees',
        expenses: 'Expenses'
    };
    pageTitle.textContent = titles[viewName] || 'SmartPesa';

    if (viewName === 'inventory') loadInventory();
    if (viewName === 'suppliers') loadSuppliers();
    if (viewName === 'transactions') loadTransactions();
    if (viewName === 'businesses') renderBusinessesGrid();
    if (viewName === 'pos') {
        loadInventory(); // this will refresh inventory and then call loadPosProducts()
        const posIdField = document.getElementById('pos-business-id');
        if (posIdField) posIdField.value = currentBusinessId;
    }
    if (viewName === 'profit') loadProfitReport();
    if (viewName === 'employees') loadEmployeesView();
    if (viewName === 'expenses') loadExpensesView();
    if (viewName === 'forecast') loadForecast();
}

navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const view = item.dataset.view;
        showView(view);
    });
});

// ============================================
// Modal Event Listeners
// ============================================

document.querySelectorAll('.modal .close').forEach(btn => {
    btn.addEventListener('click', () => btn.closest('.modal').classList.remove('active'));
});

document.getElementById('inventory-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const item = {
        name: document.getElementById('inv-name').value,
        sku: document.getElementById('inv-sku').value || null,
        quantity: parseFloat(document.getElementById('inv-quantity').value),
        unit: document.getElementById('inv-unit').value,
        price_per_unit: parseFloat(document.getElementById('inv-price').value),
        reorder_level: parseFloat(document.getElementById('inv-reorder').value)
    };
    addInventoryItem(item);
});

// Add Supplier button – open modal
document.getElementById('add-supplier-btn').addEventListener('click', () => {
    supplierModal.classList.add('active');
});

document.getElementById('supplier-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const supplier = {
        name: document.getElementById('sup-name').value,
        contact_person: document.getElementById('sup-contact').value || null,
        phone: document.getElementById('sup-phone').value || null,
        email: document.getElementById('sup-email').value || null,
        address: document.getElementById('sup-address').value || null,
        payment_terms: document.getElementById('sup-terms').value || 'Net 30'
    };
    addSupplier(supplier);
});

// Supplier payment form – now actually records payment
document.getElementById('payment-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const supplierId = parseInt(document.getElementById('payment-supplier-id').value);
    const amount = parseFloat(document.getElementById('payment-amount').value);
    const dueDate = document.getElementById('payment-due-date').value;
    const notes = document.getElementById('payment-notes').value;

    if (!supplierId || isNaN(amount) || amount <= 0) {
        showMessage('Please enter a valid amount.', 'error');
        return;
    }

    try {
        // Call the backend to record payment (this should create an expense transaction)
        await apiRequest(`/suppliers/${supplierId}/payments`, 'POST', {
            amount: amount,
            payment_date: dueDate,
            notes: notes,
            business_id: currentBusinessId
        });
        showMessage('Payment recorded successfully', 'success');
        paymentModal.classList.remove('active');
        // Refresh supplier list to update outstanding balance and recent payments
        await loadSuppliers();
        // Refresh transactions to see the new expense
        await loadTransactions();
    } catch (error) {
        showMessage(error.message, 'error');
    }
});

// ============================================
// Employee & Expense Modal Handlers
// ============================================

document.getElementById('add-rank-btn').addEventListener('click', () => {
    rankModal.classList.add('active');
});

document.getElementById('add-employee-btn').addEventListener('click', async () => {
    const ranks = await apiRequest('/employees/ranks');
    const select = document.getElementById('emp-rank');
    select.innerHTML = ranks.map(r => `<option value="${r.id}">${r.name} (${formatCurrency(r.base_salary)})</option>`).join('');
    employeeModal.classList.add('active');
});

document.getElementById('pay-salary-btn').addEventListener('click', async () => {
    const employees = await apiRequest('/employees/?active_only=true');
    const select = document.getElementById('salary-employee');
    select.innerHTML = employees.map(e => `<option value="${e.id}">${e.name}</option>`).join('');
    salaryModal.classList.add('active');
});

document.getElementById('add-expense-btn').addEventListener('click', async () => {
    // Guard: ensure a business is selected before opening the modal
    if (!currentBusinessId) {
        alert('Please select or create a business first.');
        return;
    }
    const categories = await apiRequest('/expenses/categories');
    const select = document.getElementById('expense-category');
    select.innerHTML = categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    expenseModal.classList.add('active');
});

// Rank form (create)
document.getElementById('rank-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        name: document.getElementById('rank-name').value,
        base_salary: parseFloat(document.getElementById('rank-base-salary').value),
        description: document.getElementById('rank-description').value
    };
    await apiRequest('/employees/ranks', 'POST', data);
    rankModal.classList.remove('active');
    loadRanks();
});

// Employee form (create)
document.getElementById('employee-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        name: document.getElementById('emp-name').value,
        rank_id: parseInt(document.getElementById('emp-rank').value),
        monthly_salary: parseFloat(document.getElementById('emp-salary').value),
        phone: document.getElementById('emp-phone').value,
        email: document.getElementById('emp-email').value,
        hire_date: document.getElementById('emp-hire-date').value
    };
    await apiRequest('/employees/', 'POST', data);
    employeeModal.classList.remove('active');
    loadEmployees();
    await loadTransactions();
    refreshProfitIfVisible();
});

// Salary form
document.getElementById('salary-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentBusinessId) {
        alert('Please select a business first.');
        return;
    }
    const data = {
        employee_id: parseInt(document.getElementById('salary-employee').value),
        amount: parseFloat(document.getElementById('salary-amount').value),
        payment_date: document.getElementById('salary-date').value,
        month: document.getElementById('salary-month').value,
        description: document.getElementById('salary-description').value,
        business_id: currentBusinessId
    };
    try {
        await apiRequest('/salary-payments/', 'POST', data);
        salaryModal.classList.remove('active');
        loadSalaryPayments();
        await loadTransactions();
        refreshProfitIfVisible();
        showMessage('Salary payment recorded', 'success');
    } catch (error) {
        showMessage(error.message, 'error');
    }
});

// Expense form
document.getElementById('expense-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentBusinessId) {
        alert('Please select or create a business first.');
        return;
    }
    const data = {
        category_id: parseInt(document.getElementById('expense-category').value),
        amount: parseFloat(document.getElementById('expense-amount').value),
        expense_date: document.getElementById('expense-date').value,
        description: document.getElementById('expense-description').value,
        business_id: currentBusinessId
    };
    await apiRequest('/expenses/', 'POST', data);
    expenseModal.classList.remove('active');
    loadExpenses();
    await loadTransactions();
    refreshProfitIfVisible();
});

// Edit rank form
document.getElementById('edit-rank-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    await updateRank();
});

// Edit employee form
document.getElementById('edit-employee-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    await updateEmployee();
});

// ============================================
// Business Modal Handlers
// ============================================

document.getElementById('add-business-btn').addEventListener('click', () => {
    businessModal.classList.add('active');
});

document.getElementById('business-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('business-name').value;
    const type = document.getElementById('business-type').value;
    const currency = document.getElementById('business-currency').value;
    createBusiness(name, type, currency);
});

// ============================================
// Login/Register
// ============================================

document.getElementById('login-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    login(email, password);
});

document.getElementById('register-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const confirm = document.getElementById('reg-confirm').value;
    if (password !== confirm) {
        showMessage('Passwords do not match', 'error');
        return;
    }
    register(email, password);
});

document.getElementById('show-register').addEventListener('click', (e) => {
    e.preventDefault();
    showScreen('register');
});

document.getElementById('show-login').addEventListener('click', (e) => {
    e.preventDefault();
    showScreen('login');
});

logoutBtn.addEventListener('click', () => {
    removeToken();
    stopAutoRefresh();
    showScreen('login');
});

document.getElementById('add-inventory-btn').addEventListener('click', () => {
    document.getElementById('inv-name').value = '';
    document.getElementById('inv-sku').value = '';
    document.getElementById('inv-quantity').value = 0;
    document.getElementById('inv-unit').value = 'pieces';
    document.getElementById('inv-price').value = 0;
    document.getElementById('inv-reorder').value = 10;
    document.getElementById('inv-purchase-cost').value = '';
    document.getElementById('inv-purchase-date').value = new Date().toISOString().split('T')[0];
    inventoryModal.classList.add('active');
});

// ============================================
// Global Delete Event Delegation
// ============================================
document.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-delete]');
    if (!btn) return;
    const type = btn.getAttribute('data-delete');
    const id = btn.getAttribute('data-id');
    if (!id) return;
    if (type === 'business') await deleteBusiness(id);
    if (type === 'rank') await deleteRank(id);
    if (type === 'employee') await deleteEmployee(id);
    if (type === 'inventory') await deleteInventoryItem(id);
});

// ============================================
// Initialisation
// ============================================
if (getToken()) {
    loadUserProfile().then(() => {
        loadBusinesses().then(() => {
            showScreen('dashboard');
            showView('dashboard');
            startAutoRefresh();
            initForecastControls();  // initialize forecast controls
        });
    }).catch(() => {
        removeToken();
        stopAutoRefresh();
        showScreen('login');
    });
} else {
    showScreen('login');
}