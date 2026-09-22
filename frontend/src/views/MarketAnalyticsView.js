import { adaptAnalytics, formatNumber, formatLakhs } from '../adapters/index.js';

export function renderMarketAnalyticsView(analyticsData, activeSymbol = 'NIFTY') {
  const analytics = adaptAnalytics(analyticsData);

  const maxPain = analytics?.maxPain ?? '—';
  const pcr = analytics?.pcr ?? null;
  const gex = analytics?.gex || {};
  const ivPercentile = analytics?.hasIvPercentile ? `${analyticsData.iv_percentile}%` : 'N/A';
  const ivNotice = !analytics?.hasIvPercentile;

  return `
    <div class="flex flex-col w-full text-[#E7EEF5] pb-12 bg-[#05080D]">
      <!-- 1. TOP HEADER -->
      <section class="bg-[#0C1722] rounded-xl p-5 border border-white/[0.06] shadow-xl mb-5">
        <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 pb-3 border-b border-white/[0.06]">
          <div class="flex flex-col">
            <div class="flex items-center gap-2 font-mono-xs text-[11px] mb-1">
              <span class="material-symbols-outlined text-[16px] text-[#25D9D2]">query_stats</span>
              <span class="text-[#25D9D2] font-semibold uppercase tracking-wider text-[10px]">Market Analytics & Structure</span>
              <span class="text-[#617486]">| Symbol: ${activeSymbol}</span>
            </div>
            <h1 class="text-[22px] font-bold tracking-tight text-[#E7EEF5]">Quantitative Options & Volatility Analytics</h1>
          </div>
        </div>

        <!-- ANALYTICS CARDS GRID -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 pt-4 font-mono-xs text-[11px]">
          <div class="bg-[#08111A] p-3.5 rounded-lg border border-white/[0.06]">
            <span class="text-[#617486] uppercase font-semibold text-[10px]">Put-Call Ratio (PCR)</span>
            <div class="font-mono-num text-[20px] font-bold text-[#22C997] mt-1">
              ${pcr ? formatNumber(pcr, 2) : '—'}
            </div>
            <span class="text-[#8FA4B7] text-[10px]">${pcr > 1 ? 'Bullish bias' : 'Neutral-Bullish'}</span>
          </div>

          <div class="bg-[#08111A] p-3.5 rounded-lg border border-white/[0.06]">
            <span class="text-[#617486] uppercase font-semibold text-[10px]">Max Pain Strike</span>
            <div class="font-mono-num text-[20px] font-bold text-[#F5B84B] mt-1">
              ${typeof maxPain === 'number' ? formatNumber(maxPain, 0) : maxPain}
            </div>
            <span class="text-[#8FA4B7] text-[10px]">Strike pinning center</span>
          </div>

          <div class="bg-[#08111A] p-3.5 rounded-lg border border-white/[0.06]">
            <span class="text-[#617486] uppercase font-semibold text-[10px]">IV Percentile</span>
            <div class="font-mono-num text-[20px] font-bold ${ivNotice ? 'text-[#8FA4B7]' : 'text-[#25D9D2]'} mt-1">
              ${ivPercentile}
            </div>
            <span class="text-[#8FA4B7] text-[10px]">${ivNotice ? 'Historical data insufficient' : 'Annual rank'}</span>
          </div>

          <div class="bg-[#08111A] p-3.5 rounded-lg border border-white/[0.06]">
            <span class="text-[#617486] uppercase font-semibold text-[10px]">Net Gamma (GEX)</span>
            <div class="font-mono-num text-[20px] font-bold text-[#22C997] mt-1">
              ${gex.value ? formatLakhs(gex.value) : '—'}
            </div>
            <span class="text-[#8FA4B7] text-[10px]">Dealers net position</span>
          </div>
        </div>
      </section>

      <!-- 2. ANALYTICAL BREAKDOWN SECTIONS -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-3.5">
        <!-- Support & Resistance Structure -->
        <div class="lg:col-span-6 bg-[#0C1722] rounded-xl p-4 border border-white/[0.06] shadow-lg">
          <div class="flex items-center justify-between pb-2.5 mb-3 border-b border-white/[0.06]">
            <span class="text-[13px] font-bold text-[#E7EEF5]">Key Technical & Options Boundaries</span>
            <span class="font-mono-xs text-[9px] px-2 py-0.5 rounded bg-[#25D9D2]/10 text-[#25D9D2] font-semibold">STRUCTURE</span>
          </div>

          <div class="flex flex-col gap-2 font-mono-xs text-[11px]">
            <div class="flex items-center justify-between py-1.5 border-b border-white/[0.04]">
              <span class="text-[#FF5C6C] font-semibold">Call Wall Resistance</span>
              <span class="font-mono-num font-bold text-[#E7EEF5]">${gex.call_wall || '—'}</span>
            </div>
            <div class="flex items-center justify-between py-1.5 border-b border-white/[0.04]">
              <span class="text-[#25D9D2] font-semibold">Gamma Flip Level</span>
              <span class="font-mono-num font-bold text-[#E7EEF5]">${gex.gamma_flip || '—'}</span>
            </div>
            <div class="flex items-center justify-between py-1.5 border-b border-white/[0.04]">
              <span class="text-[#F5B84B] font-semibold">Max Pain Pin Target</span>
              <span class="font-mono-num font-bold text-[#E7EEF5]">${gex.pin_target || maxPain}</span>
            </div>
            <div class="flex items-center justify-between py-1.5">
              <span class="text-[#22C997] font-semibold">Put Wall Support</span>
              <span class="font-mono-num font-bold text-[#E7EEF5]">${gex.put_wall || '—'}</span>
            </div>
          </div>
        </div>

        <!-- Volatility Notice Card -->
        <div class="lg:col-span-6 bg-[#0C1722] rounded-xl p-4 border border-white/[0.06] shadow-lg flex flex-col justify-between">
          <div class="flex items-center justify-between pb-2.5 mb-3 border-b border-white/[0.06]">
            <span class="text-[13px] font-bold text-[#E7EEF5]">Implied Volatility Assessment</span>
            <span class="font-mono-xs text-[9px] px-2 py-0.5 rounded bg-[#071019] text-[#8FA4B7] border border-white/[0.06]">STATUS</span>
          </div>

          <div class="p-4 bg-[#08111A] rounded-lg border border-white/[0.05] font-mono-xs text-[11px] leading-relaxed text-[#8FA4B7]">
            ${ivNotice ? `
              <div class="flex items-start gap-2">
                <span class="material-symbols-outlined text-[18px] text-[#F5B84B] shrink-0">info</span>
                <div>
                  <strong class="text-[#E7EEF5] block mb-1">IV Percentile Notice</strong>
                  Historical IV percentile calculation requires extended historical volatility datasets. Displaying <strong>N/A</strong> per production feed protocol.
                </div>
              </div>
            ` : `
              Implied Volatility structure is operating within expected historical range.
            `}
          </div>
        </div>
      </div>
    </div>
  `;
}
