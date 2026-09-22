import { adaptMarketBar, formatNumber, formatLakhs } from '../adapters/index.js';

export function renderHeader(activeTab, rawMarketList, alertCount = 0, healthData = null) {
  const market = adaptMarketBar(rawMarketList);

  const nifty = market.find(m => m.symbol === 'NIFTY') || { priceFormatted: 'UNAVAILABLE', changePctFormatted: '—', changePtsFormatted: '—', isUp: true, isUnavailable: true };
  const bankNifty = market.find(m => m.symbol === 'BANKNIFTY') || { priceFormatted: 'UNAVAILABLE', changePctFormatted: '—', changePtsFormatted: '—', isUp: true, isUnavailable: true };
  const sensex = market.find(m => m.symbol === 'SENSEX') || { priceFormatted: 'UNAVAILABLE', changePctFormatted: '—', changePtsFormatted: '—', isUp: true, isUnavailable: true };
  const vix = market.find(m => m.symbol === 'INDIAVIX') || { priceFormatted: 'UNAVAILABLE', changePctFormatted: '—', changePtsFormatted: '—', isUp: false, isUnavailable: true };

  const tabLabels = {
    overview: 'OVERVIEW [NSE:IN]',
    options: 'OPTION CHAIN MATRIX [NSE:IN]',
    expiry: 'EXPIRY INTELLIGENCE & GEX [NSE:IN]',
    analytics: 'MARKET ANALYTICS & STRUCTURE [NSE:IN]',
    news: 'NEWS & INSIGHTS FEED [NSE:IN]',
    watchlist: 'QUANT WATCHLIST SCANNER [NSE:IN]',
    alerts: 'VOLATILITY & ALERTS TERMINAL [NSE:IN]',
    settings: 'SETTINGS & SYSTEM DIAGNOSTICS [NSE:IN]'
  };

  const currentTabLabel = tabLabels[activeTab] || 'DESK [NSE:IN]';

  const isLiveMode = healthData?.data_mode === 'live';
  const statusLabel = isLiveMode ? 'Live Market' : (healthData ? 'Simulated Feed' : 'Connecting...');
  const statusColor = isLiveMode ? 'bg-[#22C997] text-[#22C997]' : 'bg-[#F5B84B] text-[#F5B84B]';

  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' });
  const timeStr = now.toLocaleTimeString('en-US', { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' });

  return `
    <header class="fixed top-0 left-64 right-0 h-24 bg-[#071019]/95 backdrop-blur-md z-40 border-b border-white/[0.06] flex flex-col select-none">
      <!-- TOP SEARCH & STATUS BAR -->
      <div class="h-14 px-6 flex items-center justify-between border-b border-white/[0.04]">
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-1.5 text-[#617486] font-mono-xs text-[11px] tracking-wider">
            <span class="material-symbols-outlined text-[15px] text-[#25D9D2]">radar</span>
            <span class="text-[#8FA4B7]">TERMINAL</span>
            <span class="text-[#617486]">/</span>
            <span class="text-[#E7EEF5] font-semibold">${currentTabLabel}</span>
          </div>
        </div>

        <div class="flex-1 max-w-xl mx-8">
          <div class="relative flex items-center w-full">
            <span class="material-symbols-outlined absolute left-3 text-[16px] text-[#617486] pointer-events-none">search</span>
            <input 
              id="global-search-input"
              type="text" 
              placeholder="Search symbols (NIFTY, BANKNIFTY), strikes, GEX, news..." 
              class="w-full bg-[#08111A] border border-white/[0.08] rounded px-4 pl-9 py-1.5 text-[#E7EEF5] font-mono-sm text-[12px] placeholder:text-[#617486] focus:outline-none focus:border-[#25D9D2]/50 transition-colors"
            />
          </div>
        </div>

        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 px-3 py-1 bg-[#0C1722] border border-white/[0.06] rounded-full">
            <span class="inline-block w-2 h-2 rounded-full ${statusColor.split(' ')[0]} shadow-[0_0_6px_rgba(34,201,151,0.4)] animate-pulse"></span>
            <span class="${statusColor.split(' ')[1]} font-mono-xs text-[11px] font-semibold tracking-wide">${statusLabel}</span>
          </div>

          <div class="text-[#8FA4B7] font-mono-xs text-[11px] hidden sm:flex items-center gap-1.5">
            <span>${dateStr}</span>
            <span class="text-[#617486]">•</span>
            <span class="text-[#E7EEF5]">${timeStr}</span>
          </div>

          <button id="btn-alerts-toggle" type="button" class="relative p-1.5 text-[#8FA4B7] hover:text-[#E7EEF5] hover:bg-[#0C1722] rounded-full transition-colors">
            <span class="material-symbols-outlined text-[20px]">notifications</span>
            ${alertCount > 0 ? `
              <span class="absolute top-0.5 right-0.5 w-3.5 h-3.5 bg-[#FF5C6C] text-white font-mono-xs text-[9px] rounded-full flex items-center justify-center leading-none font-bold">
                ${alertCount}
              </span>
            ` : ''}
          </button>

          <div class="w-7 h-7 rounded-full bg-[#25D9D2]/20 border border-[#25D9D2]/40 flex items-center justify-center text-[#25D9D2] font-bold font-mono-sm text-[12px]">
            QD
          </div>
        </div>
      </div>

      <!-- TICKER BAR -->
      <div class="h-10 px-6 flex items-center justify-between bg-[#050B12]/80 text-[#E7EEF5] font-mono-sm text-[11px] overflow-x-auto whitespace-nowrap">
        <div class="flex items-center gap-7">
          <!-- NIFTY 50 -->
          <div class="flex items-center gap-2">
            <span class="font-semibold text-[#8FA4B7] text-[11px]">NIFTY 50</span>
            <span class="text-[#E7EEF5] font-bold font-mono-num">${nifty.priceFormatted}</span>
            <span class="${nifty.isUp ? 'text-[#22C997]' : 'text-[#FF5C6C]'} font-mono-xs text-[10px] font-medium">
              ${nifty.changePctFormatted} (${nifty.changePtsFormatted})
            </span>
          </div>

          <!-- BANK NIFTY -->
          <div class="flex items-center gap-2">
            <span class="font-semibold text-[#8FA4B7] text-[11px]">BANK NIFTY</span>
            <span class="text-[#E7EEF5] font-bold font-mono-num">${bankNifty.priceFormatted}</span>
            <span class="${bankNifty.isUp ? 'text-[#22C997]' : 'text-[#FF5C6C]'} font-mono-xs text-[10px] font-medium">
              ${bankNifty.changePctFormatted} (${bankNifty.changePtsFormatted})
            </span>
          </div>

          <!-- SENSEX -->
          <div class="flex items-center gap-2">
            <span class="font-semibold text-[#8FA4B7] text-[11px]">SENSEX</span>
            <span class="text-[#E7EEF5] font-bold font-mono-num">${sensex.priceFormatted}</span>
            <span class="${sensex.isUp ? 'text-[#22C997]' : 'text-[#FF5C6C]'} font-mono-xs text-[10px] font-medium">
              ${sensex.changePctFormatted} (${sensex.changePtsFormatted})
            </span>
          </div>

          <!-- INDIA VIX -->
          <div class="flex items-center gap-2">
            <span class="font-semibold text-[#8FA4B7] text-[11px]">INDIA VIX</span>
            <span class="text-[#E7EEF5] font-bold font-mono-num">${vix.priceFormatted}</span>
            <span class="${vix.isUp ? 'text-[#FF5C6C]' : 'text-[#22C997]'} font-mono-xs text-[10px] font-medium">
              ${vix.changePctFormatted}
            </span>
          </div>
        </div>

        <div class="flex items-center gap-5 pl-4 border-l border-white/[0.08] text-[#8FA4B7]">
          <div class="flex items-center gap-1.5">
            <span class="text-[#617486] font-mono-xs text-[10px] uppercase">DATA FEED:</span>
            <span class="text-[#25D9D2] font-mono-num font-bold text-[11px]">${statusLabel.toUpperCase()}</span>
          </div>
        </div>
      </div>
    </header>
  `;
}
