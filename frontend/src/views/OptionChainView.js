import { adaptOptionChain, formatNumber, formatLakhs } from '../adapters/index.js';

export function renderOptionChainView(chainData, expiriesData, activeSymbol = 'NIFTY') {
  const chain = adaptOptionChain(chainData);
  const expiries = Array.isArray(expiriesData?.expiries) ? expiriesData.expiries : [];
  const currentExpiry = chain.expiry || expiries[0] || null;

  const spot = chain.spotPrice;
  const pcr = chain.pcr;
  const maxPain = chain.maxPain;
  const atm = chain.atmStrike;

  return `
    <div class="flex flex-col w-full text-[#E7EEF5] pb-8 bg-[#05080D]">
      <!-- 1. TOP CONTROLS & UNDERLYING SELECTOR -->
      <div class="w-full bg-[#05080D] p-3 flex flex-col gap-2.5">
        <div class="flex flex-wrap items-center justify-between gap-3 pb-2.5 border-b border-white/[0.06]">
          <!-- Instrument Switcher -->
          <div class="flex items-center gap-1 bg-[#071019] p-1 rounded-lg border border-white/[0.06]">
            <button 
              id="opt-sym-nifty" 
              type="button" 
              class="px-3 py-1 ${activeSymbol === 'NIFTY' ? 'bg-[#101C28] text-[#25D9D2] border border-[#25D9D2]/30 font-bold' : 'text-[#8FA4B7] hover:text-[#E7EEF5]'} font-mono-xs text-[12px] rounded transition-colors"
            >
              NIFTY 50
            </button>
            <button 
              id="opt-sym-banknifty" 
              type="button" 
              class="px-3 py-1 ${activeSymbol === 'BANKNIFTY' ? 'bg-[#101C28] text-[#25D9D2] border border-[#25D9D2]/30 font-bold' : 'text-[#8FA4B7] hover:text-[#E7EEF5]'} font-mono-xs text-[12px] rounded transition-colors"
            >
              BANK NIFTY
            </button>
          </div>

          <!-- Underlying Spot Summary -->
          <div class="flex items-center gap-4 bg-[#0C1722] px-3.5 py-1.5 rounded-lg border border-white/[0.06]">
            <div class="flex flex-col">
              <span class="font-mono-xs text-[9px] text-[#617486] uppercase tracking-wider font-medium">UNDERLYING SPOT</span>
              <div class="flex items-baseline gap-2">
                <span class="font-mono-num text-[18px] font-bold text-[#E7EEF5]">${chain.spotFormatted}</span>
              </div>
            </div>
            <div class="w-px h-6 bg-white/[0.08]"></div>
            <div class="flex flex-col">
              <span class="font-mono-xs text-[9px] text-[#617486] uppercase tracking-wider font-medium">ATM STRIKE</span>
              <span class="font-mono-num text-[12px] font-semibold text-[#25D9D2]">${atm || '—'}</span>
            </div>
          </div>

          <!-- Expiry Dropdown Selector -->
          <div class="flex items-center gap-2">
            <div class="flex items-center gap-1.5 bg-[#0C1722] px-3 py-1.5 rounded-lg border border-white/[0.06]">
              <span class="material-symbols-outlined text-[15px] text-[#25D9D2]">event</span>
              <span class="font-mono-xs text-[10px] text-[#617486] uppercase font-semibold">EXPIRY:</span>
              <select id="opt-expiry-select" class="bg-[#071019] text-[#25D9D2] font-mono-xs text-[11px] font-bold px-2 py-0.5 rounded border border-[#25D9D2]/30 focus:outline-none">
                ${expiries.length === 0 ? `<option value="">${currentExpiry || 'N/A'}</option>` : expiries.map(exp => `
                  <option value="${exp}" ${exp === currentExpiry ? 'selected' : ''}>${exp}</option>
                `).join('')}
              </select>
            </div>
          </div>
        </div>

        <!-- SUMMARY METRICS BAR -->
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 pt-0.5">
          <div class="bg-[#0C1722] p-2.5 rounded-lg border border-white/[0.06]">
            <span class="font-mono-xs text-[9px] text-[#617486] font-semibold uppercase">PCR (OI)</span>
            <div class="font-mono-num text-[15px] font-bold text-[#22C997] mt-0.5">${pcr ? formatNumber(pcr, 2) : '—'}</div>
          </div>
          <div class="bg-[#0C1722] p-2.5 rounded-lg border border-white/[0.06]">
            <span class="font-mono-xs text-[9px] text-[#617486] font-semibold uppercase">MAX PAIN</span>
            <div class="font-mono-num text-[15px] font-bold text-[#F5B84B] mt-0.5">${maxPain ? formatNumber(maxPain, 0) : '—'}</div>
          </div>
          <div class="bg-[#0C1722] p-2.5 rounded-lg border border-white/[0.06]">
            <span class="font-mono-xs text-[9px] text-[#617486] font-semibold uppercase">ATM STRIKE</span>
            <div class="font-mono-num text-[15px] font-bold text-[#25D9D2] mt-0.5">${atm || '—'}</div>
          </div>
          <div class="bg-[#0C1722] p-2.5 rounded-lg border border-white/[0.06]">
            <span class="font-mono-xs text-[9px] text-[#617486] font-semibold uppercase">NET GEX</span>
            <div class="font-mono-num text-[15px] font-bold text-[#22C997] mt-0.5">${chain.netGex ? formatLakhs(chain.netGex) : '—'}</div>
          </div>
          <div class="bg-[#0C1722] p-2.5 rounded-lg border border-white/[0.06]">
            <span class="font-mono-xs text-[9px] text-[#617486] font-semibold uppercase">TOTAL STRIKES</span>
            <div class="font-mono-num text-[15px] font-bold text-[#E7EEF5] mt-0.5">${chain.strikes.length}</div>
          </div>
          <div class="bg-[#0C1722] p-2.5 rounded-lg border border-white/[0.06]">
            <span class="font-mono-xs text-[9px] text-[#617486] font-semibold uppercase">DATA FEED</span>
            <div class="font-mono-num text-[12px] font-bold text-[#22C997] mt-1">${chain.isUnavailable ? 'UNAVAILABLE' : 'LIVE FEED'}</div>
          </div>
        </div>
      </div>

      <!-- 2. FULL OPTION CHAIN STRIKE MATRIX TABLE -->
      <div class="w-full bg-[#060D15] overflow-x-auto border-t border-b border-white/[0.06] relative shadow-lg min-h-[400px]">
        ${chain.isUnavailable ? `
          <div class="p-12 text-center flex flex-col items-center justify-center text-[#617486]">
            <span class="material-symbols-outlined text-[36px] mb-2 text-[#FF5C6C]">table_rows</span>
            <span class="font-bold text-[14px] text-[#E7EEF5]">MARKET DATA FEED UNAVAILABLE</span>
            <p class="font-mono-xs text-[11px] text-[#8FA4B7] mt-1">Connect your live broker API or market feed to view real-time option chain strikes.</p>
          </div>
        ` : `
          <!-- Sticky Table Header -->
          <div class="sticky top-0 z-30 bg-[#071019] grid grid-cols-[1fr_150px_1fr] text-[#617486] font-mono-xs text-[10px] border-b border-white/[0.06] min-w-[900px]">
            <div class="grid grid-cols-5 px-3 py-2 text-right items-center bg-[#071019]">
              <span class="uppercase text-left font-bold text-[#FF5C6C]">CALL GREEKS</span>
              <span class="uppercase">IV</span>
              <span class="uppercase">VOL</span>
              <span class="uppercase">CALL OI</span>
              <span class="uppercase pr-1 font-bold text-[#E7EEF5]">LTP (₹)</span>
            </div>

            <div class="py-2 text-center font-bold text-[#25D9D2] tracking-wider bg-[#0C1722] flex items-center justify-center gap-1 border-x border-white/[0.06]">
              <span class="material-symbols-outlined text-[14px]">unfold_more</span>
              <span>STRIKE PRICE</span>
            </div>

            <div class="grid grid-cols-5 px-3 py-2 text-left items-center bg-[#071019]">
              <span class="uppercase pl-1 font-bold text-[#E7EEF5]">LTP (₹)</span>
              <span class="uppercase">PUT OI</span>
              <span class="uppercase text-right">VOL</span>
              <span class="uppercase text-right">IV</span>
              <span class="text-right font-bold text-[#22C997] uppercase pr-1">PUT GREEKS</span>
            </div>
          </div>

          <!-- Rows Container -->
          <div class="flex flex-col font-mono-xs text-[11px] divide-y divide-white/[0.03] min-w-[900px]">
            ${chain.strikes.map(row => {
              const isAtm = row.isAtm;
              const isPain = row.isMaxPain;
              const bgClass = isAtm ? 'bg-[#25D9D2]/10 border-y border-[#25D9D2]/30' : (isPain ? 'bg-[#F5B84B]/5' : 'hover:bg-[#0C1722]/50');

              return `
                <div class="grid grid-cols-[1fr_150px_1fr] items-center ${bgClass} transition-colors">
                  <!-- CE Details -->
                  <div class="grid grid-cols-5 px-3 py-1.5 text-right items-center">
                    <div class="text-left text-[#8FA4B7] text-[10px]">${row.ce.delta ? `${formatNumber(row.ce.delta, 2)}` : '—'}</div>
                    <div class="text-[#8FA4B7]">${row.ce.ivFormatted}</div>
                    <div class="text-[#E7EEF5]">${row.ce.volumeFormatted}</div>
                    <div class="font-bold text-[#FF5C6C]">${row.ce.oiFormatted}</div>
                    <div class="pr-1 font-bold text-[#E7EEF5]">${row.ce.ltpFormatted}</div>
                  </div>

                  <!-- Strike Center Column -->
                  <div class="py-1.5 text-center bg-[#071019] font-bold border-x border-white/[0.06] flex items-center justify-center gap-1 ${isAtm ? 'text-[#25D9D2]' : (isPain ? 'text-[#F5B84B]' : 'text-[#E7EEF5]')}">
                    ${isAtm ? '<span class="text-[8px] px-1 py-0.2 bg-[#25D9D2]/20 text-[#25D9D2] rounded font-bold">ATM</span>' : ''}
                    ${isPain ? '<span class="text-[8px] px-1 py-0.2 bg-[#F5B84B]/20 text-[#F5B84B] rounded font-bold">PAIN</span>' : ''}
                    <span class="text-[12px] font-mono-num">${row.strike}</span>
                  </div>

                  <!-- PE Details -->
                  <div class="grid grid-cols-5 px-3 py-1.5 text-left items-center">
                    <div class="pl-1 font-bold text-[#E7EEF5]">${row.pe.ltpFormatted}</div>
                    <div class="font-bold text-[#22C997]">${row.pe.oiFormatted}</div>
                    <div class="text-right text-[#E7EEF5]">${row.pe.volumeFormatted}</div>
                    <div class="text-right text-[#8FA4B7]">${row.pe.ivFormatted}</div>
                    <div class="text-right text-[#8FA4B7] text-[10px]">${row.pe.delta ? `${formatNumber(row.pe.delta, 2)}` : '—'}</div>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        `}
      </div>
    </div>
  `;
}
