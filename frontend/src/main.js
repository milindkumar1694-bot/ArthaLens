import { getHealth, getMarketBar } from './api/market.js';
import { getExpiries, getOptionChain } from './api/options.js';
import { getExpiryIntel } from './api/expiry.js';
import { getAnalytics } from './api/analytics.js';
import { getNewsIntel } from './api/news.js';
import { getWatchlist } from './api/watchlist.js';
import { API_BASE_URL } from './api/client.js';

import { renderHeader } from './components/Header.js';
import { renderSidebar } from './components/Sidebar.js';
import { renderAlertsDrawer } from './components/AlertsDrawer.js';
import { renderSettingsModal } from './components/SettingsModal.js';

import { renderOverviewView } from './views/OverviewView.js';
import { renderOptionChainView } from './views/OptionChainView.js';
import { renderExpiryIntelView } from './views/ExpiryIntelView.js';
import { renderMarketAnalyticsView } from './views/MarketAnalyticsView.js';
import { renderNewsIntelView } from './views/NewsIntelView.js';
import { renderWatchlistView } from './views/WatchlistView.js';
import { renderAlertsView } from './views/AlertsView.js';

let activeTab = 'overview';
let activeSymbol = 'NIFTY';
let activeExpiry = null;
let activeAlertFilter = 'ALL';
let isAlertsDrawerOpen = false;
let isSettingsModalOpen = false;

let state = {
  health: null,
  market: [],
  expiries: null,
  chain: null,
  expiryIntel: null,
  analytics: null,
  newsIntel: null,
  watchlist: null,
  loading: false,
  error: null
};

async function loadData() {
  state.loading = true;
  try {
    const [health, market] = await Promise.all([getHealth(), getMarketBar()]);
    state.health = health;
    state.market = market;

    if (activeTab === 'overview') {
      const [expIntel, newsData] = await Promise.all([
        getExpiryIntel(activeSymbol).catch(() => null),
        getNewsIntel(activeSymbol).catch(() => null)
      ]);
      state.expiryIntel = expIntel;
      state.newsIntel = newsData;
    } else if (activeTab === 'options') {
      const expiriesData = await getExpiries(activeSymbol).catch(() => null);
      state.expiries = expiriesData;
      const targetExpiry = activeExpiry || expiriesData?.expiries?.[0] || null;
      state.chain = await getOptionChain(activeSymbol, targetExpiry).catch(() => null);
    } else if (activeTab === 'expiry') {
      state.expiryIntel = await getExpiryIntel(activeSymbol, activeExpiry).catch(() => null);
    } else if (activeTab === 'analytics') {
      state.analytics = await getAnalytics(activeSymbol, activeExpiry).catch(() => null);
    } else if (activeTab === 'news') {
      state.newsIntel = await getNewsIntel(activeSymbol).catch(() => null);
    } else if (activeTab === 'watchlist') {
      state.watchlist = await getWatchlist().catch(() => null);
    } else if (activeTab === 'alerts') {
      state.expiryIntel = await getExpiryIntel(activeSymbol).catch(() => null);
    }

    state.loading = false;
    state.error = null;
    render();
  } catch (err) {
    state.loading = false;
    state.error = err.message;
    render();
  }
}

function renderContent() {
  if (state.error) {
    return `
      <div class="p-5 bg-[#0C1722] border border-[#FF5C6C] text-[#E7EEF5] m-4 font-mono-xs rounded-lg">
        <b class="text-[#FF5C6C] text-[14px] block mb-1">API CONNECTION NOTICE</b>
        ${state.error}
        <div class="mt-2 text-[#8FA4B7]">
          The ArthaLens dashboard is attempting to reconnect to backend services at ${API_BASE_URL}.
        </div>
      </div>
    `;
  }

  if (activeTab === 'overview') return renderOverviewView(state);
  if (activeTab === 'options') return renderOptionChainView(state.chain, state.expiries, activeSymbol);
  if (activeTab === 'expiry') return renderExpiryIntelView(state.expiryIntel, activeSymbol);
  if (activeTab === 'analytics') return renderMarketAnalyticsView(state.analytics, activeSymbol);
  if (activeTab === 'news') return renderNewsIntelView(state.newsIntel, activeSymbol);
  if (activeTab === 'watchlist') return renderWatchlistView(state.watchlist);
  if (activeTab === 'alerts') return renderAlertsView(state.expiryIntel?.alerts || [], activeAlertFilter);

  return renderOverviewView(state);
}

function render() {
  const alertCount = state.expiryIntel?.alerts?.length || 0;
  const sidebarHtml = renderSidebar(activeTab, state.health);
  const headerHtml = renderHeader(activeTab, state.market, alertCount, state.health);
  const alertsDrawerHtml = renderAlertsDrawer(isAlertsDrawerOpen, state.expiryIntel?.alerts || []);
  const settingsModalHtml = renderSettingsModal(isSettingsModalOpen, state.health);
  const mainHtml = renderContent();

  document.querySelector('#app').innerHTML = `
    ${sidebarHtml}
    <div class="pl-64 flex flex-col min-h-screen">
      ${headerHtml}
      ${alertsDrawerHtml}
      ${settingsModalHtml}
      <main class="relative pt-24 bg-[#05080D] w-full px-gutter min-h-screen">
        ${mainHtml}
      </main>
    </div>
  `;

  // Attach Event Listeners
  document.querySelectorAll('[data-tab]').forEach(btn => {
    btn.onclick = (e) => {
      e.preventDefault();
      activeTab = btn.dataset.tab;
      loadData();
    };
  });

  // Settings & Diagnostics Triggers
  const openSettingsBtn = document.querySelector('#btn-open-settings');
  if (openSettingsBtn) {
    openSettingsBtn.onclick = () => { isSettingsModalOpen = true; render(); };
  }

  const openDiagBtn = document.querySelector('#btn-open-diagnostics');
  if (openDiagBtn) {
    openDiagBtn.onclick = () => { isSettingsModalOpen = true; render(); };
  }

  const closeSettingsBtn = document.querySelector('#btn-close-settings');
  if (closeSettingsBtn) {
    closeSettingsBtn.onclick = () => { isSettingsModalOpen = false; render(); };
  }

  const dismissSettingsBtn = document.querySelector('#btn-dismiss-settings');
  if (dismissSettingsBtn) {
    dismissSettingsBtn.onclick = () => { isSettingsModalOpen = false; render(); };
  }

  // Alert Drawer Triggers
  const alertsBtn = document.querySelector('#btn-alerts-toggle');
  if (alertsBtn) {
    alertsBtn.onclick = () => { isAlertsDrawerOpen = !isAlertsDrawerOpen; render(); };
  }

  const closeAlertsBtn = document.querySelector('#btn-close-alerts');
  if (closeAlertsBtn) {
    closeAlertsBtn.onclick = () => { isAlertsDrawerOpen = false; render(); };
  }

  const ackAlertsBtn = document.querySelector('#btn-ack-alerts');
  if (ackAlertsBtn) {
    ackAlertsBtn.onclick = () => { isAlertsDrawerOpen = false; render(); };
  }

  // Instrument Selectors
  const optSymNifty = document.querySelector('#opt-sym-nifty');
  if (optSymNifty) {
    optSymNifty.onclick = () => { activeSymbol = 'NIFTY'; activeExpiry = null; loadData(); };
  }

  const optSymBankNifty = document.querySelector('#opt-sym-banknifty');
  if (optSymBankNifty) {
    optSymBankNifty.onclick = () => { activeSymbol = 'BANKNIFTY'; activeExpiry = null; loadData(); };
  }

  // Expiry Dropdown
  const optExpirySelect = document.querySelector('#opt-expiry-select');
  if (optExpirySelect) {
    optExpirySelect.onchange = (e) => { activeExpiry = e.target.value; loadData(); };
  }

  // Alert Filter Buttons
  document.querySelectorAll('[data-alert-filter]').forEach(btn => {
    btn.onclick = () => {
      activeAlertFilter = btn.dataset.alertFilter;
      render();
    };
  });
}

// Initial Data Load & Auto-Refresh
loadData();
setInterval(loadData, 15000);
