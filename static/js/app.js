/**
 * B2B Supply Chain and Inventory Tracking Portal
 * Frontend Single Page Application Engine with Role-Based Authentication
 */

const API_BASE = '/api';

// Application State
const AppState = {
  currentUser: null,  // { id, username, company: { id, name, company_type, ... }, role_title }
  activeTab: 'dashboard',
  inventory: [],
  products: [],
  categories: [],
  suppliers: [],
  orders: [],
  scoringConfig: { w1: 0.40, w2: 0.35, w3: 0.25 },
  supplierLeaderboard: [],
  criticalAlerts: []
};

// Toast Notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer') || createToastContainer();
  const toast = document.createElement('div');
  toast.className = 'toast';
  
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'danger') icon = '⚠️';
  if (type === 'warning') icon = '🔔';

  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function createToastContainer() {
  const container = document.createElement('div');
  container.id = 'toastContainer';
  container.className = 'toast-container';
  document.body.appendChild(container);
  return container;
}

// ---------------------------------------------------------------------------
// AUTHENTICATION SYSTEM
// ---------------------------------------------------------------------------

async function checkAuthStatus() {
  try {
    const res = await fetch(`${API_BASE}/accounts/auth/me/`);
    const data = await res.json();

    if (data.authenticated && data.user) {
      handleSuccessfulAuth(data.user);
    } else {
      showAuthOverlay(true);
    }
  } catch (err) {
    console.warn("Auth check error, displaying login overlay:", err);
    showAuthOverlay(true);
  }
}

function showAuthOverlay(show = true) {
  const overlay = document.getElementById('authOverlay');
  if (overlay) {
    overlay.style.display = show ? 'flex' : 'none';
  }
}

function switchAuthTab(tab) {
  const btnLogin = document.getElementById('tabBtnLogin');
  const btnReg = document.getElementById('tabBtnRegister');
  const formLogin = document.getElementById('authLoginForm');
  const formReg = document.getElementById('authRegisterForm');

  if (tab === 'login') {
    if (btnLogin) btnLogin.classList.add('active');
    if (btnReg) btnReg.classList.remove('active');
    if (formLogin) formLogin.style.display = 'block';
    if (formReg) formReg.style.display = 'none';
  } else {
    if (btnReg) btnReg.classList.add('active');
    if (btnLogin) btnLogin.classList.remove('active');
    if (formReg) formReg.style.display = 'block';
    if (formLogin) formLogin.style.display = 'none';
  }
}

function selectRegisterRole(role) {
  const roleInput = document.getElementById('regRoleType');
  if (roleInput) roleInput.value = role;

  const cardSme = document.getElementById('roleCardSME');
  const cardSup = document.getElementById('roleCardSUPPLIER');

  if (role === 'SME') {
    if (cardSme) cardSme.classList.add('selected');
    if (cardSup) cardSup.classList.remove('selected');
  } else {
    if (cardSup) cardSup.classList.add('selected');
    if (cardSme) cardSme.classList.remove('selected');
  }
}

async function quickFillLogin(username, password) {
  const uInput = document.getElementById('loginUsername');
  const pInput = document.getElementById('loginPassword');
  if (uInput) uInput.value = username;
  if (pInput) pInput.value = password;

  await performLogin(username, password);
}

async function performLogin(username, password) {
  try {
    const res = await fetch(`${API_BASE}/accounts/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (res.ok && data.user) {
      showToast(`Welcome, ${data.user.username}!`, 'success');
      handleSuccessfulAuth(data.user);
    } else {
      showToast(data.error || 'Invalid username or password.', 'danger');
    }
  } catch (err) {
    showToast('Login network request failed.', 'danger');
  }
}

function setupAuthHandlers() {
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('loginUsername')?.value;
      const password = document.getElementById('loginPassword')?.value;
      if (username && password) {
        await performLogin(username, password);
      }
    });
  }

  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        role_type: document.getElementById('regRoleType')?.value || 'SME',
        company_name: document.getElementById('regCompanyName')?.value,
        contact_person: document.getElementById('regContactPerson')?.value,
        tax_id: document.getElementById('regTaxId')?.value,
        email: document.getElementById('regEmail')?.value,
        phone: document.getElementById('regPhone')?.value,
        username: document.getElementById('regUsername')?.value,
        password: document.getElementById('regPassword')?.value,
      };

      try {
        const res = await fetch(`${API_BASE}/accounts/auth/register/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (res.ok && data.user) {
          showToast('Account and Company profile created successfully!', 'success');
          handleSuccessfulAuth(data.user);
        } else {
          showToast(data.error || 'Registration failed.', 'danger');
        }
      } catch (err) {
        showToast('Registration error occurred.', 'danger');
      }
    });
  }
}

async function performLogout() {
  try {
    await fetch(`${API_BASE}/accounts/auth/logout/`, { method: 'POST' });
  } catch (e) {}
  AppState.currentUser = null;
  showToast('You have been signed out.', 'info');
  showAuthOverlay(true);
}

function handleSuccessfulAuth(user) {
  AppState.currentUser = user;
  showAuthOverlay(false);
  applyUserRoleLayout(user);
  loadAllData();
}

function applyUserRoleLayout(user) {
  const isSme = user.company ? user.company.company_type === 'SME' : true;
  const companyName = user.company ? user.company.name : 'Enterprise';
  
  const elCompTitle = document.getElementById('headerCompanyTitle');
  if (elCompTitle) elCompTitle.innerText = `${companyName} (${isSme ? 'Buyer / KOBİ Portal' : 'Supplier Operations Portal'})`;

  const elSub = document.getElementById('headerSubtitle');
  if (elSub) elSub.innerText = isSme 
    ? 'Critical Stockout Alerts, Procurement Automation & Supplier Performance'
    : 'Order Fulfillment, Shipment Status Updates & Performance Scorecard';

  const elTopComp = document.getElementById('topbarCompanyName');
  if (elTopComp) elTopComp.innerText = companyName;

  const roleBadge = document.getElementById('topbarRoleBadge');
  if (roleBadge) {
    roleBadge.innerText = isSme ? '🏢 Buyer (SME)' : '🏭 Supplier (Vendor)';
    roleBadge.style.color = isSme ? '#60A5FA' : '#FBBF24';
  }

  const btnPo = document.getElementById('btnCreatePoTopbar');
  if (btnPo) {
    btnPo.style.display = isSme ? 'inline-flex' : 'none';
  }

  const elSideUser = document.getElementById('sidebarUsername');
  if (elSideUser) elSideUser.innerText = user.username;

  const elSideRole = document.getElementById('sidebarUserRole');
  if (elSideRole) elSideRole.innerText = user.role_title || (isSme ? 'Procurement' : 'Operations');

  const elAvatar = document.getElementById('sidebarAvatar');
  if (elAvatar) elAvatar.innerText = (user.username.slice(0, 2) || 'US').toUpperCase();

  const navInventory = document.getElementById('navItemInventory');
  const navOrdersLabel = document.getElementById('navOrdersLabel');
  const navScoringLabel = document.getElementById('navScoringLabel');

  if (isSme) {
    if (navInventory) navInventory.style.display = 'flex';
    if (navOrdersLabel) navOrdersLabel.innerText = 'Purchase Orders';
    if (navScoringLabel) navScoringLabel.innerText = 'Supplier Scoring';
  } else {
    if (navInventory) navInventory.style.display = 'none';
    if (navOrdersLabel) navOrdersLabel.innerText = 'Incoming Orders';
    if (navScoringLabel) navScoringLabel.innerText = 'My Scorecard & Tier';
  }
}

// ---------------------------------------------------------------------------
// DATA LOADING & RENDERING
// ---------------------------------------------------------------------------

async function loadAllData() {
  try {
    await Promise.all([
      fetchInventory(),
      fetchProducts(),
      fetchSuppliers(),
      fetchOrders(),
      fetchScoringConfig()
    ]);

    renderDashboard();
    renderInventoryTable();
    renderOrdersTable();
    simulateScores();
  } catch (error) {
    console.error("Error loading data:", error);
  }
}

// Navigation Tabs
function setupNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTab = item.getAttribute('data-tab');
      if (targetTab) switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  AppState.activeTab = tabId;
  
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.getAttribute('data-tab') === tabId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.remove('active');
  });
  
  const activePane = document.getElementById(`tab-${tabId}`);
  if (activePane) {
    activePane.classList.add('active');
  }

  if (tabId === 'inventory') renderInventoryTable();
  if (tabId === 'orders') renderOrdersTable();
  if (tabId === 'scoring') simulateScores();
}

// Fetch APIs
async function fetchInventory() {
  try {
    const res = await fetch(`${API_BASE}/inventory/items/`);
    const data = await res.json();
    AppState.inventory = data.results || data || [];

    const alertRes = await fetch(`${API_BASE}/inventory/items/critical_alerts/`);
    const alertData = await alertRes.json();
    AppState.criticalAlerts = alertData.alerts || [];
    
    const alertBadge = document.getElementById('sidebarAlertBadge');
    if (alertBadge) {
      alertBadge.innerText = AppState.criticalAlerts.length;
      alertBadge.style.display = AppState.criticalAlerts.length > 0 ? 'inline-block' : 'none';
    }
  } catch (e) {
    console.error("fetchInventory error:", e);
  }
}

async function fetchProducts() {
  try {
    const res = await fetch(`${API_BASE}/inventory/products/`);
    const data = await res.json();
    AppState.products = data.results || data || [];

    const catRes = await fetch(`${API_BASE}/inventory/categories/`);
    const catData = await catRes.json();
    AppState.categories = catData.results || catData || [];
  } catch (e) {
    console.error("fetchProducts error:", e);
  }
}

async function fetchSuppliers() {
  try {
    const res = await fetch(`${API_BASE}/accounts/companies/suppliers/`);
    AppState.suppliers = await res.json();
  } catch (e) {
    console.error("fetchSuppliers error:", e);
  }
}

async function fetchOrders() {
  try {
    const res = await fetch(`${API_BASE}/orders/purchase-orders/`);
    const data = await res.json();
    let orders = data.results || data || [];

    if (AppState.currentUser && AppState.currentUser.company) {
      const comp = AppState.currentUser.company;
      if (comp.company_type === 'SUPPLIER') {
        orders = orders.filter(o => o.supplier_company === comp.id || (o.supplier_company_details && o.supplier_company_details.id === comp.id));
      }
    }

    AppState.orders = orders;
  } catch (e) {
    console.error("fetchOrders error:", e);
  }
}

async function fetchScoringConfig() {
  try {
    const res = await fetch(`${API_BASE}/scoring/configurations/`);
    const data = await res.json();
    const configs = data.results || data || [];
    if (configs.length > 0) {
      AppState.scoringConfig = {
        w1: configs[0].w1_timeliness,
        w2: configs[0].w2_completeness,
        w3: configs[0].w3_price_consistency
      };
    }
  } catch (e) {
    console.error("fetchScoringConfig error:", e);
  }
}

// ---------------------------------------------------------------------------
// DASHBOARD
// ---------------------------------------------------------------------------

function renderDashboard() {
  const isSme = AppState.currentUser?.company ? AppState.currentUser.company.company_type === 'SME' : true;

  const totalSkus = AppState.inventory.length;
  const criticalCount = AppState.criticalAlerts.length;
  const healthyCount = AppState.inventory.filter(i => !i.is_critical).length;
  const pendingOrders = AppState.orders.filter(o => o.status === 'PENDING_SUPPLIER' || o.status === 'CONFIRMED' || o.status === 'IN_TRANSIT').length;
  
  let valuation = 0;
  AppState.inventory.forEach(item => {
    valuation += item.current_stock * parseFloat(item.product.unit_price);
  });

  const healthRate = totalSkus > 0 ? Math.round((healthyCount / totalSkus) * 100) : 100;

  const elSkus = document.getElementById('statTotalSkus');
  if (elSkus) elSkus.innerText = totalSkus;

  const elCrit = document.getElementById('statCriticalCount');
  if (elCrit) elCrit.innerText = criticalCount;

  const elHealth = document.getElementById('statHealthRate');
  if (elHealth) elHealth.innerText = `${healthRate}%`;

  const elPending = document.getElementById('statPendingOrders');
  if (elPending) elPending.innerText = pendingOrders;

  const elVal = document.getElementById('statValuation');
  if (elVal) elVal.innerText = `$${valuation.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

  // Critical Alert Banner Container
  const alertContainer = document.getElementById('criticalAlertBannerContainer');
  if (alertContainer) {
    if (isSme && criticalCount > 0) {
      alertContainer.innerHTML = `
        <div class="critical-alert-box">
          <div class="alert-left">
            <div class="alert-icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
              </svg>
            </div>
            <div class="alert-info">
              <h3>CRITICAL STOCK ALERT: ${criticalCount} Product(s) Below Safety Threshold</h3>
              <p>Immediate replenishment is recommended to prevent assembly disruptions.</p>
            </div>
          </div>
          <button class="btn btn-danger" onclick="switchTab('inventory'); filterCriticalStock();">
            Review Low Stock Items &rarr;
          </button>
        </div>
      `;
    } else if (!isSme) {
      alertContainer.innerHTML = `
        <div style="background: rgba(37, 99, 235, 0.1); border: 1px solid rgba(37, 99, 235, 0.25); border-radius: 12px; padding: 14px 20px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between;">
          <span style="color: #93C5FD; font-size: 0.88rem; font-weight: 600;">🏭 Supplier Fulfillment Hub: You have ${pendingOrders} order(s) in your pipeline.</span>
          <button class="btn btn-primary btn-sm" onclick="switchTab('orders')">View Incoming Orders</button>
        </div>
      `;
    } else {
      alertContainer.innerHTML = `
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 12px; padding: 14px 20px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between;">
          <span style="color: #34D399; font-size: 0.88rem; font-weight: 600;">✨ All inventory levels are healthy. No critical threshold violations detected.</span>
          <button class="btn btn-secondary btn-sm" onclick="switchTab('inventory')">View Inventory</button>
        </div>
      `;
    }
  }

  // Recent Orders on Dashboard
  const recentOrdersTbody = document.getElementById('dashboardRecentOrdersTbody');
  if (recentOrdersTbody) {
    const recent = AppState.orders.slice(0, 5);
    if (recent.length === 0) {
      recentOrdersTbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 20px;">No recent orders.</td></tr>`;
    } else {
      recentOrdersTbody.innerHTML = recent.map(o => `
        <tr>
          <td><strong>${o.order_number}</strong></td>
          <td>${o.supplier_company_details ? o.supplier_company_details.name : 'Supplier'}</td>
          <td>$${parseFloat(o.total_amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
          <td>${getStatusBadge(o.status, o.status_display)}</td>
          <td>${o.expected_delivery_date}</td>
          <td>
            <a href="/api/orders/purchase-orders/${o.id}/pdf/" target="_blank" class="btn btn-secondary btn-sm">
              📄 PDF
            </a>
          </td>
        </tr>
      `).join('');
    }
  }
}

// ---------------------------------------------------------------------------
// INVENTORY
// ---------------------------------------------------------------------------

function renderInventoryTable(filter = 'ALL') {
  const tbody = document.getElementById('inventoryTableBody');
  if (!tbody) return;

  let items = AppState.inventory;
  if (filter === 'CRITICAL') {
    items = items.filter(i => i.is_critical);
  }

  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 30px;">No inventory records match this filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = items.map(item => {
    const healthBadge = item.is_critical
      ? `<span class="badge badge-critical">🚨 CRITICAL (${item.current_stock} &le; ${item.critical_threshold})</span>`
      : `<span class="badge badge-healthy">🟢 HEALTHY</span>`;

    return `
      <tr>
        <td>
          <strong>${item.product.name}</strong><br/>
          <span style="font-size: 0.72rem; color: var(--text-muted); font-family: monospace;">${item.product.sku}</span>
        </td>
        <td>${item.product.category_name || 'General'}</td>
        <td>
          <div style="display: flex; align-items: center; gap: 8px;">
            <button class="btn btn-secondary btn-sm" onclick="adjustStock(${item.id}, -5)">-5</button>
            <strong style="font-size: 1rem; color: ${item.is_critical ? '#F87171' : '#F8FAFC'};">${item.current_stock}</strong>
            <button class="btn btn-secondary btn-sm" onclick="adjustStock(${item.id}, +10)">+10</button>
          </div>
          <span style="font-size: 0.72rem; color: var(--text-muted);">${item.product.unit}</span>
        </td>
        <td>${item.critical_threshold} ${item.product.unit}</td>
        <td>${healthBadge}</td>
        <td>${item.product.preferred_supplier_name || 'Not assigned'}</td>
        <td>
          <div style="display: flex; gap: 6px;">
            ${item.is_critical ? `
              <button class="btn btn-danger btn-sm" onclick="quickReorder(${item.id})">
                ⚡ Auto Reorder (+${item.reorder_quantity})
              </button>
            ` : `
              <button class="btn btn-secondary btn-sm" onclick="openOrderModalWithProduct(${item.product.id})">
                + Order
              </button>
            `}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function filterCriticalStock() {
  const filterSelect = document.getElementById('inventoryFilterSelect');
  if (filterSelect) filterSelect.value = 'CRITICAL';
  renderInventoryTable('CRITICAL');
}

async function adjustStock(itemId, delta) {
  try {
    const res = await fetch(`${API_BASE}/inventory/items/${itemId}/adjust_stock/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ delta })
    });
    const data = await res.json();
    showToast(data.message, delta > 0 ? 'success' : 'warning');
    await fetchInventory();
    renderDashboard();
    renderInventoryTable(document.getElementById('inventoryFilterSelect')?.value || 'ALL');
  } catch (err) {
    showToast('Failed to update stock', 'danger');
  }
}

async function quickReorder(itemId) {
  try {
    const res = await fetch(`${API_BASE}/orders/purchase-orders/quick_reorder/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ inventory_item_id: itemId })
    });
    if (res.ok) {
      const order = await res.json();
      showToast(`Purchase Order ${order.order_number} generated successfully!`, 'success');
      await fetchOrders();
      renderDashboard();
      switchTab('orders');
    } else {
      const err = await res.json();
      showToast(err.error || 'Could not place reorder', 'danger');
    }
  } catch (err) {
    showToast('Error sending reorder request', 'danger');
  }
}

// ---------------------------------------------------------------------------
// ORDERS & INVOICES
// ---------------------------------------------------------------------------

function renderOrdersTable(filter = 'ALL') {
  const tbody = document.getElementById('ordersTableBody');
  if (!tbody) return;

  const isSupplier = AppState.currentUser?.company?.company_type === 'SUPPLIER';

  const btnNewPoInTab = document.getElementById('btnNewOrderInTab');
  if (btnNewPoInTab) {
    btnNewPoInTab.style.display = isSupplier ? 'none' : 'inline-flex';
  }

  let orders = AppState.orders;
  if (filter !== 'ALL') {
    orders = orders.filter(o => o.status === filter);
  }

  if (orders.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 30px;">No purchase orders found for this account.</td></tr>`;
    return;
  }

  tbody.innerHTML = orders.map(o => {
    let actionButtons = `
      <a href="/api/orders/purchase-orders/${o.id}/pdf/" target="_blank" class="btn btn-secondary btn-sm" title="View Purchase Order PDF">
        📄 PO PDF
      </a>
    `;

    if (o.invoice) {
      actionButtons += `
        <a href="/api/orders/invoices/${o.invoice.id}/pdf/" target="_blank" class="btn btn-secondary btn-sm" style="color: #34D399;" title="View Invoice PDF">
          🧾 Invoice
        </a>
      `;
    } else if (o.status === 'DELIVERED' || o.status === 'IN_TRANSIT') {
      actionButtons += `
        <button class="btn btn-secondary btn-sm" onclick="generateInvoiceForOrder(${o.id})">
          + Invoice
        </button>
      `;
    }

    if (isSupplier) {
      if (o.status === 'PENDING_SUPPLIER') {
        actionButtons += `<button class="btn btn-primary btn-sm" onclick="updateOrderStatus(${o.id}, 'CONFIRMED')">🤝 Confirm</button>`;
      } else if (o.status === 'CONFIRMED') {
        actionButtons += `<button class="btn btn-primary btn-sm" onclick="updateOrderStatus(${o.id}, 'IN_TRANSIT')">🚚 Ship</button>`;
      } else if (o.status === 'IN_TRANSIT') {
        actionButtons += `<button class="btn btn-success btn-sm" onclick="updateOrderStatus(${o.id}, 'DELIVERED')">✓ Mark Delivered</button>`;
      }
    } else {
      if (o.status === 'IN_TRANSIT') {
        actionButtons += `<button class="btn btn-success btn-sm" onclick="updateOrderStatus(${o.id}, 'DELIVERED')">📦 Receive & Restock</button>`;
      }
    }

    return `
      <tr>
        <td><strong>${o.order_number}</strong></td>
        <td>
          <span style="font-size: 0.85rem; font-weight: 600;">${o.supplier_company_details?.name || 'Supplier'}</span><br/>
          <span style="font-size: 0.72rem; color: var(--text-muted);">Buyer: ${o.buyer_company_details?.name || 'SME'}</span>
        </td>
        <td>
          <strong>$${parseFloat(o.total_amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}</strong>
        </td>
        <td>${getStatusBadge(o.status, o.status_display)}</td>
        <td>${o.expected_delivery_date}</td>
        <td>${o.actual_delivery_date || '<span style="color: var(--text-muted);">-</span>'}</td>
        <td>
          <div style="display: flex; gap: 6px; flex-wrap: wrap;">
            ${actionButtons}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function getStatusBadge(status, label) {
  switch (status) {
    case 'DELIVERED':
      return `<span class="badge badge-healthy">✓ ${label}</span>`;
    case 'IN_TRANSIT':
      return `<span class="badge badge-info">🚚 ${label}</span>`;
    case 'CONFIRMED':
      return `<span class="badge badge-warning">🤝 ${label}</span>`;
    case 'PENDING_SUPPLIER':
      return `<span class="badge badge-warning">⏳ ${label}</span>`;
    default:
      return `<span class="badge badge-silver">${label}</span>`;
  }
}

async function updateOrderStatus(orderId, newStatus) {
  try {
    const res = await fetch(`${API_BASE}/orders/purchase-orders/${orderId}/update_status/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    showToast(data.message, 'success');
    await fetchOrders();
    await fetchInventory();
    renderDashboard();
    renderOrdersTable();
    simulateScores();
  } catch (err) {
    showToast('Failed to update status', 'danger');
  }
}

async function generateInvoiceForOrder(orderId) {
  try {
    const res = await fetch(`${API_BASE}/orders/purchase-orders/${orderId}/generate_invoice/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();
    showToast(data.message, 'success');
    await fetchOrders();
    renderOrdersTable();
  } catch (err) {
    showToast('Failed to generate invoice', 'danger');
  }
}

// ---------------------------------------------------------------------------
// SUPPLIER SCORING
// ---------------------------------------------------------------------------

function setupScoringSliders() {
  const w1Slider = document.getElementById('sliderW1');
  const w2Slider = document.getElementById('sliderW2');
  const w3Slider = document.getElementById('sliderW3');

  if (!w1Slider) return;

  const updateSimulation = () => {
    const w1 = parseFloat(w1Slider.value);
    const w2 = parseFloat(w2Slider.value);
    const w3 = parseFloat(w3Slider.value);

    const elW1 = document.getElementById('valW1');
    if (elW1) elW1.innerText = `${Math.round(w1 * 100)}%`;

    const elW2 = document.getElementById('valW2');
    if (elW2) elW2.innerText = `${Math.round(w2 * 100)}%`;

    const elW3 = document.getElementById('valW3');
    if (elW3) elW3.innerText = `${Math.round(w3 * 100)}%`;

    AppState.scoringConfig = { w1, w2, w3 };
    simulateScores();
  };

  w1Slider.addEventListener('input', updateSimulation);
  w2Slider.addEventListener('input', updateSimulation);
  w3Slider.addEventListener('input', updateSimulation);
}

async function simulateScores() {
  const { w1, w2, w3 } = AppState.scoringConfig;
  try {
    const res = await fetch(`${API_BASE}/scoring/evaluations/simulate/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ w1, w2, w3 })
    });
    const data = await res.json();
    AppState.supplierLeaderboard = data.leaderboard || [];
    renderLeaderboard();
  } catch (err) {
    console.error('Error simulating scores:', err);
  }
}

function renderLeaderboard() {
  const container = document.getElementById('supplierLeaderboardContainer');
  if (!container) return;

  const isSupplier = AppState.currentUser?.company?.company_type === 'SUPPLIER';
  const myCompanyId = AppState.currentUser?.company?.id;

  let items = AppState.supplierLeaderboard;
  
  const slidersBox = document.getElementById('buyerScoringControlsBox');
  if (slidersBox) {
    slidersBox.style.display = isSupplier ? 'none' : 'block';
  }

  if (isSupplier) {
    const myScorecard = items.find(s => s.supplier_id === myCompanyId) || items[0];
    if (myScorecard) {
      container.innerHTML = `
        <div class="card-section" style="border: 2px solid #3B82F6; background: rgba(30, 41, 59, 0.7); margin-bottom: 24px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <div>
              <span class="badge badge-info" style="margin-bottom: 6px;">Your Official Supplier Scorecard</span>
              <h2 style="font-size: 1.4rem; font-weight: 800;">${myScorecard.supplier_name}</h2>
              <p style="font-size: 0.8rem; color: var(--text-secondary);">
                Evaluated by Buyer SMEs across all completed purchase orders.
              </p>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 2.6rem; font-weight: 900; color: #60A5FA;">
                ${myScorecard.overall_score.toFixed(1)}%
              </div>
              <span class="badge badge-gold" style="font-size: 0.85rem; padding: 6px 14px;">${myScorecard.tier}</span>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-top: 20px;">
            <div style="background: var(--bg-card); padding: 16px; border-radius: 10px; border: 1px solid var(--border-subtle);">
              <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 6px;">
                <span style="color: var(--text-secondary);">Delivery Timeliness ($W_1$)</span>
                <strong>${myScorecard.timeliness_score.toFixed(1)}%</strong>
              </div>
              <div class="progress-container">
                <div class="progress-fill" style="width: ${myScorecard.timeliness_score}%; background-color: #3B82F6;"></div>
              </div>
              <span style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px; display: block;">${myScorecard.on_time_count} on-time deliveries</span>
            </div>

            <div style="background: var(--bg-card); padding: 16px; border-radius: 10px; border: 1px solid var(--border-subtle);">
              <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 6px;">
                <span style="color: var(--text-secondary);">Order Completeness ($W_2$)</span>
                <strong>${myScorecard.completeness_score.toFixed(1)}%</strong>
              </div>
              <div class="progress-container">
                <div class="progress-fill" style="width: ${myScorecard.completeness_score}%; background-color: #10B981;"></div>
              </div>
              <span style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px; display: block;">Fulfilled qty accuracy</span>
            </div>

            <div style="background: var(--bg-card); padding: 16px; border-radius: 10px; border: 1px solid var(--border-subtle);">
              <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 6px;">
                <span style="color: var(--text-secondary);">Price Consistency ($W_3$)</span>
                <strong>${myScorecard.price_consistency_score.toFixed(1)}%</strong>
              </div>
              <div class="progress-container">
                <div class="progress-fill" style="width: ${myScorecard.price_consistency_score}%; background-color: #F59E0B;"></div>
              </div>
              <span style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px; display: block;">Adherence to catalog prices</span>
            </div>
          </div>
        </div>
      `;
      return;
    }
  }

  container.innerHTML = items.map((sup, idx) => {
    let tierBadgeClass = 'badge-gold';
    if (sup.tier.includes('Silver')) tierBadgeClass = 'badge-silver';
    if (sup.tier.includes('Bronze')) tierBadgeClass = 'badge-bronze';
    if (sup.tier.includes('Restricted')) tierBadgeClass = 'badge-critical';

    const rankMedal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `#${idx + 1}`;

    return `
      <div class="card-section" style="margin-bottom: 16px; border-left: 4px solid ${idx === 0 ? '#F59E0B' : '#3B82F6'};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
          <div>
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
              <span style="font-size: 1.2rem;">${rankMedal}</span>
              <h3 style="font-size: 1.1rem; font-weight: 700;">${sup.supplier_name}</h3>
              <span class="badge ${tierBadgeClass}">${sup.tier}</span>
            </div>
            <p style="font-size: 0.78rem; color: var(--text-muted);">
              Contact: ${sup.contact_person || 'N/A'} | Tax ID: ${sup.tax_id || 'N/A'} | Email: ${sup.email || 'N/A'}
            </p>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 2rem; font-weight: 900; color: #60A5FA; letter-spacing: -0.04em;">
              ${sup.overall_score.toFixed(1)}%
            </div>
            <span style="font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600;">Overall Score</span>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px;">
          <div style="background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px; border: 1px solid var(--border-subtle);">
            <div style="display: flex; justify-content: space-between; font-size: 0.78rem; margin-bottom: 4px;">
              <span style="color: var(--text-secondary);">Delivery Timeliness</span>
              <strong>${sup.timeliness_score.toFixed(1)}%</strong>
            </div>
            <div class="progress-container">
              <div class="progress-fill" style="width: ${sup.timeliness_score}%; background-color: #3B82F6;"></div>
            </div>
          </div>

          <div style="background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px; border: 1px solid var(--border-subtle);">
            <div style="display: flex; justify-content: space-between; font-size: 0.78rem; margin-bottom: 4px;">
              <span style="color: var(--text-secondary);">Order Completeness</span>
              <strong>${sup.completeness_score.toFixed(1)}%</strong>
            </div>
            <div class="progress-container">
              <div class="progress-fill" style="width: ${sup.completeness_score}%; background-color: #10B981;"></div>
            </div>
          </div>

          <div style="background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px; border: 1px solid var(--border-subtle);">
            <div style="display: flex; justify-content: space-between; font-size: 0.78rem; margin-bottom: 4px;">
              <span style="color: var(--text-secondary);">Price Consistency</span>
              <strong>${sup.price_consistency_score.toFixed(1)}%</strong>
            </div>
            <div class="progress-container">
              <div class="progress-fill" style="width: ${sup.price_consistency_score}%; background-color: #F59E0B;"></div>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// ---------------------------------------------------------------------------
// MODALS & FORMS
// ---------------------------------------------------------------------------

function setupForms() {
  const addProductForm = document.getElementById('addProductForm');
  if (addProductForm) {
    addProductForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const productPayload = {
        name: document.getElementById('prodName')?.value,
        sku: document.getElementById('prodSku')?.value,
        category: parseInt(document.getElementById('prodCategory')?.value || 1),
        unit: document.getElementById('prodUnit')?.value || 'Pieces',
        unit_price: parseFloat(document.getElementById('prodPrice')?.value || 0),
        preferred_supplier: parseInt(document.getElementById('prodSupplier')?.value || 1)
      };

      try {
        const prodRes = await fetch(`${API_BASE}/inventory/products/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(productPayload)
        });
        const createdProd = await prodRes.json();

        const buyerCompId = AppState.currentUser?.company?.id || 1;
        await fetch(`${API_BASE}/inventory/items/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            company: buyerCompId,
            product_id: createdProd.id,
            current_stock: parseInt(document.getElementById('prodInitialStock')?.value || 0),
            critical_threshold: parseInt(document.getElementById('prodThreshold')?.value || 20),
            reorder_quantity: parseInt(document.getElementById('prodReorderQty')?.value || 100),
            warehouse_location: document.getElementById('prodLocation')?.value || 'Main Warehouse'
          })
        });

        showToast('New Product added to Catalog & Inventory!', 'success');
        closeModal('addProductModal');
        await fetchInventory();
        await fetchProducts();
        renderDashboard();
        renderInventoryTable();
      } catch (err) {
        showToast('Error creating product', 'danger');
      }
    });
  }

  const newOrderForm = document.getElementById('newOrderForm');
  if (newOrderForm) {
    newOrderForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const supplierId = parseInt(document.getElementById('orderSupplierSelect')?.value);
      const prodId = parseInt(document.getElementById('orderProductSelect')?.value);
      const qty = parseInt(document.getElementById('orderQuantity')?.value || 1);
      const prod = AppState.products.find(p => p.id === prodId);

      const buyerCompId = AppState.currentUser?.company?.id || 1;

      const orderPayload = {
        order_number: `PO-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`,
        order_type: 'PURCHASE_ORDER',
        buyer_company: buyerCompId,
        supplier_company: supplierId,
        status: 'PENDING_SUPPLIER',
        notes: document.getElementById('orderNotes')?.value || '',
        items: [
          {
            product_id: prodId,
            quantity_requested: qty,
            agreed_unit_price: prod ? prod.unit_price : 10.00
          }
        ]
      };

      try {
        const res = await fetch(`${API_BASE}/orders/purchase-orders/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(orderPayload)
        });
        if (res.ok) {
          showToast('Purchase order created successfully!', 'success');
          closeModal('newOrderModal');
          await fetchOrders();
          renderDashboard();
          renderOrdersTable();
          switchTab('orders');
        }
      } catch (err) {
        showToast('Error submitting order', 'danger');
      }
    });
  }
}

function openModal(modalId) {
  if (modalId === 'addProductModal') {
    const catSelect = document.getElementById('prodCategory');
    if (catSelect) catSelect.innerHTML = AppState.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    const supSelect = document.getElementById('prodSupplier');
    if (supSelect) supSelect.innerHTML = AppState.suppliers.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  }

  if (modalId === 'newOrderModal') {
    const supSelect = document.getElementById('orderSupplierSelect');
    if (supSelect) supSelect.innerHTML = AppState.suppliers.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
    const prodSelect = document.getElementById('orderProductSelect');
    if (prodSelect) prodSelect.innerHTML = AppState.products.map(p => `<option value="${p.id}">${p.name} ($${p.unit_price})</option>`).join('');
  }

  const el = document.getElementById(modalId);
  if (el) el.classList.add('show');
}

function closeModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) el.classList.remove('show');
}

function openOrderModalWithProduct(productId) {
  openModal('newOrderModal');
  const select = document.getElementById('orderProductSelect');
  if (select) select.value = productId;
}

// ---------------------------------------------------------------------------
// GLOBAL EXPORTS ON WINDOW
// ---------------------------------------------------------------------------
window.switchAuthTab = switchAuthTab;
window.selectRegisterRole = selectRegisterRole;
window.quickFillLogin = quickFillLogin;
window.performLogout = performLogout;
window.switchTab = switchTab;
window.openModal = openModal;
window.closeModal = closeModal;
window.adjustStock = adjustStock;
window.quickReorder = quickReorder;
window.filterCriticalStock = filterCriticalStock;
window.updateOrderStatus = updateOrderStatus;
window.generateInvoiceForOrder = generateInvoiceForOrder;
window.simulateScores = simulateScores;
window.openOrderModalWithProduct = openOrderModalWithProduct;
window.renderInventoryTable = renderInventoryTable;

// Initialize on load
document.addEventListener('DOMContentLoaded', async () => {
  setupNavigation();
  setupScoringSliders();
  setupForms();
  setupAuthHandlers();
  await checkAuthStatus();
});
