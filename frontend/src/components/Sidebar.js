export function renderSidebar(activeTab, healthData) {
  const isHealthy = healthData && healthData.status === 'ok';
  const dataMode = healthData?.data_mode || 'mock';
  const provider = healthData?.provider || 'simulated';

  const navItems = [
    { id: 'overview', label: 'Overview', icon: 'grid_view' },
    { id: 'options', label: 'Option Chain', icon: 'table_chart' },
    { id: 'expiry', label: 'Expiry Intelligence', icon: 'analytics' },
    { id: 'analytics', label: 'Market Analytics', icon: 'query_stats' },
    { id: 'news', label: 'News & Insights', icon: 'newspaper' },
    { id: 'watchlist', label: 'Watchlist Scanner', icon: 'candlestick_chart' },
    { id: 'alerts', label: 'Volatility & Alerts', icon: 'notifications_active' },
  ];

  const navHtml = navItems.map(item => {
    const isActive = activeTab === item.id;
    const activeClass = isActive
      ? 'bg-[#0C1722] text-[#25D9D2] border-l-2 border-[#25D9D2] font-semibold'
      : 'text-[#8FA4B7] hover:bg-[#0C1722]/70 hover:text-[#E7EEF5]';

    const iconColor = isActive ? 'text-[#25D9D2]' : 'text-[#617486]';

    return `
      <a data-tab="${item.id}" href="#" class="flex items-center gap-3 px-3.5 py-2.5 transition-colors rounded text-[13px] ${activeClass}">
        <span class="material-symbols-outlined text-[18px] ${iconColor}">${item.icon}</span>
        <span>${item.label}</span>
      </a>
    `;
  }).join('');

  return `
    <aside class="fixed left-0 top-0 bottom-0 w-64 bg-[#04090F] border-r border-white/[0.06] z-50 flex flex-col justify-between select-none">
      <div class="flex flex-col">
        <!-- BRAND HEADER -->
        <div class="p-4 flex items-center gap-3 border-b border-white/[0.06] bg-[#060D15]">
          <div class="w-7 h-7 rounded bg-[#25D9D2]/20 border border-[#25D9D2]/40 flex items-center justify-center text-[#25D9D2] font-bold font-mono-sm text-[13px]">
            AL
          </div>
          <div class="flex flex-col min-w-0 flex-1">
            <div class="flex items-center justify-between">
              <span class="font-headline-sm text-[13px] font-bold tracking-tight text-[#E7EEF5] uppercase leading-none">ArthaLens</span>
              <span class="font-mono-xs text-[9px] px-1.5 py-0.5 bg-[#0C1722] text-[#25D9D2] border border-[#25D9D2]/25 rounded">v2.4 PRO</span>
            </div>
            <span class="font-mono-xs text-[10px] text-[#617486] truncate mt-1">See Beyond the Noise.</span>
          </div>
        </div>

        <!-- SECTION TITLE -->
        <div class="px-4 pt-3.5 pb-1.5">
          <span class="font-mono-xs text-[10px] uppercase tracking-wider text-[#617486] font-semibold">Terminal Desks</span>
        </div>

        <!-- NAVIGATION -->
        <nav class="flex flex-col px-2.5 gap-1">
          ${navHtml}
        </nav>
      </div>

      <!-- FOOTER DIAGNOSTICS & SYSTEM STATUS -->
      <div class="p-3.5 border-t border-white/[0.06] bg-[#060D15]/80 flex flex-col gap-2">
        <div class="flex items-center justify-between px-2.5 py-1.5 font-mono-xs text-[10px] bg-[#04090F] border border-white/[0.06] rounded">
          <div class="flex items-center gap-1.5">
            <span class="inline-block w-1.5 h-1.5 rounded-full ${isHealthy ? 'bg-[#22C997]' : 'bg-[#FF5C6C]'}"></span>
            <span class="${isHealthy ? 'text-[#22C997]' : 'text-[#FF5C6C]'} font-semibold tracking-wider">${dataMode.toUpperCase()}</span>
            <span class="text-[#617486]">| ${provider}</span>
          </div>
          <span class="text-[#8FA4B7]">18ms</span>
        </div>

        <div class="flex items-center justify-between pt-1 px-1">
          <button id="btn-open-settings" type="button" class="flex items-center gap-1.5 text-[#8FA4B7] hover:text-[#E7EEF5] transition-colors text-[11px]">
            <span class="material-symbols-outlined text-[15px] text-[#617486]">settings</span>
            <span>Settings</span>
          </button>
          <button id="btn-open-diagnostics" type="button" class="flex items-center gap-1.5 text-[#8FA4B7] hover:text-[#E7EEF5] transition-colors text-[11px]">
            <span class="material-symbols-outlined text-[15px] text-[#617486]">terminal</span>
            <span>Diagnostics</span>
          </button>
        </div>
      </div>
    </aside>
  `;
}
