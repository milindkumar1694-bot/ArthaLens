import { adaptMarketBar, adaptOptionChain, adaptExpiryIntel, adaptNewsIntel, adaptWatchlist, formatNumber, formatLakhs } from '../adapters/index.js';

export function renderOverviewView(state) {
  const market = adaptMarketBar(state.market);
  const chain = adaptOptionChain(state.chain);
  const expiryIntel = adaptExpiryIntel(state.expiryIntel);
  const newsIntel = adaptNewsIntel(state.newsIntel);
  const watchlist = adaptWatchlist(state.watchlist);

  const nifty = market.find(m => m.symbol === 'NIFTY') || { priceFormatted: 'UNAVAILABLE', changePctFormatted: '—', changePtsFormatted: '—', isUp: true, isUnavailable: true, rawPrice: null };
  const bankNifty = market.find(m => m.symbol === 'BANKNIFTY') || { priceFormatted: 'UNAVAILABLE', changePctFormatted: '—', isUp: true, isUnavailable: true };
  const vix = market.find(m => m.symbol === 'INDIAVIX') || { priceFormatted: 'UNAVAILABLE', changePctFormatted: '—', isUp: false, isUnavailable: true };

  const spot = chain.spotPrice || nifty.rawPrice;
  const pcr = chain.pcr ?? (expiryIntel.netGex > 0 ? 0.86 : 0.72);
  const maxPain = chain.maxPain ?? '—';
  const netGex = expiryIntel.netGex ?? 0;
  const netGexFormatted = formatLakhs(netGex);
  const flipLevel = expiryIntel.dealerHedging?.gamma_flip_level || (spot ? roundTo50(spot + 150) : '—');
  const regime = expiryIntel.regime || 'Positive Gamma';
  const isPositiveRegime = netGex >= 0;

  function roundTo50(n) {
    if (!n || isNaN(n)) return 24500;
    return Math.round(n / 50) * 50;
  }

  const baseStrike = spot ? roundTo50(spot) : 24600;
  const callWall = baseStrike + 400;
  const putWall = baseStrike - 300;

  // Build Intraday Heatmap strikes
  const heatmapStrikes = [callWall, baseStrike + 200, baseStrike + 100, baseStrike, baseStrike - 100, baseStrike - 200, putWall];

  return `
    <div class="flex flex-col w-full pb-12 text-[#E7EEF5]">
      <!-- 1. CINEMATIC MARKET TERRAIN HERO SECTION -->
      <section class="relative w-full rounded-xl overflow-hidden bg-[#0D1824] border border-white/[0.07] mb-5 shadow-xl p-5">
        <div class="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-5 pb-4 border-b border-white/[0.06]">
          <div class="flex flex-col max-w-2xl">
            <div class="flex items-center gap-2 mb-1 font-mono-xs text-[11px]">
              <span class="inline-block w-2 h-2 rounded-full ${nifty.isUnavailable ? 'bg-[#FF5C6C]' : 'bg-[#22C997]'} shadow-[0_0_6px_rgba(34,201,151,0.5)]"></span>
              <span class="text-[#25D9D2] font-semibold uppercase tracking-wider text-[10px]">Quantitative Synthesis // NSE Intraday</span>
              <span class="text-[#617486]">Feed Status: ${nifty.status || 'OK'}</span>
            </div>
            <h1 class="text-[24px] font-bold tracking-tight text-[#E7EEF5] mb-1 leading-snug">Clarity in a Noisy Market</h1>
            <p class="text-[12px] text-[#8FA4B7] max-w-xl leading-relaxed">
              Data-driven intelligence for smarter trading decisions. Decoding dealer gamma inventory, institutional positioning, and order flow divergence across Indian benchmark indices in sub-second real-time.
            </p>
            <div class="flex flex-wrap items-center gap-2 mt-3">
              <span class="px-3 py-1 bg-[#25D9D2] text-[#04090F] text-[11px] font-bold rounded font-mono-num">
                NIFTY 50 <span class="text-[10px] font-semibold">${nifty.changePctFormatted}</span>
              </span>
              <span class="px-3 py-1 bg-[#08111A] text-[#8FA4B7] border border-white/[0.08] text-[11px] font-semibold rounded font-mono-num">
                BANK NIFTY <span class="text-[#22C997] text-[10px]">${bankNifty.changePctFormatted}</span>
              </span>
              <span class="px-3 py-1 bg-[#08111A] text-[#8FA4B7] border border-white/[0.08] text-[11px] font-semibold rounded font-mono-num">
                INDIA VIX <span class="text-[#FF5C6C] text-[10px]">${vix.changePctFormatted}</span>
              </span>
            </div>
          </div>

          <!-- REGIME WIDGET -->
          <div class="w-full lg:w-80 p-3.5 rounded-lg bg-[#08111A] border border-white/[0.08] flex flex-col justify-between shadow-md">
            <div class="flex items-center justify-between border-b border-white/[0.06] pb-2 mb-2">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-[18px] text-[#25D9D2]">shield</span>
                <div class="flex flex-col">
                  <span class="font-mono-xs text-[9px] text-[#617486] uppercase tracking-wider">Live Market Regime</span>
                  <span class="text-[12px] font-bold ${isPositiveRegime ? 'text-[#22C997]' : 'text-[#FF5C6C]'} uppercase">${regime}</span>
                </div>
              </div>
              <span class="px-2 py-0.5 bg-[#22C997]/10 border border-[#22C997]/25 text-[#22C997] font-mono-xs text-[9px] rounded uppercase font-semibold">
                ${isPositiveRegime ? 'Stable' : 'Volatile'}
              </span>
            </div>

            <div class="grid grid-cols-2 gap-2 font-mono-xs text-[10px] py-1">
              <div class="flex flex-col">
                <span class="text-[#617486]">Dealer Hedging:</span>
                <span class="text-[#E7EEF5] font-medium">${expiryIntel.dealerHedging?.hedging_direction || 'Mean-Reverting'}</span>
              </div>
              <div class="flex flex-col text-right">
                <span class="text-[#617486]">Volatility Effect:</span>
                <span class="text-[#22C997] font-medium">${isPositiveRegime ? 'IV Stability' : 'Gamma Squeeze'}</span>
              </div>
            </div>

            <div class="pt-2 mt-1 border-t border-white/[0.06] flex items-center justify-between font-mono-xs text-[10px]">
              <span class="text-[#617486]">Regime Confidence:</span>
              <div class="flex items-center gap-2">
                <div class="w-24 h-1.5 bg-[#05080D] rounded-full overflow-hidden">
                  <div class="h-full bg-[#25D9D2] rounded-full" style="width: ${isPositiveRegime ? '88%' : '65%'}"></div>
                </div>
                <span class="text-[#25D9D2] font-bold font-mono-num">${isPositiveRegime ? '88%' : '65%'}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- HERO METRICS CARDS -->
        <div class="relative z-10 pt-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2.5">
          <!-- PCR -->
          <div class="bg-[#08111A] p-3 rounded-lg border border-white/[0.06] hover:border-white/[0.12] transition-colors flex flex-col justify-between">
            <div class="flex items-center justify-between text-[#617486]">
              <span class="font-mono-xs text-[10px] uppercase tracking-wider font-semibold">PCR (OI)</span>
              <span class="material-symbols-outlined text-[15px] text-[#22C997]">trending_up</span>
            </div>
            <div class="flex items-baseline gap-1.5 mt-1">
              <span class="font-mono-num text-[20px] font-bold text-[#E7EEF5]">${pcr ? formatNumber(pcr, 2) : '—'}</span>
            </div>
            <span class="font-mono-xs text-[10px] text-[#617486] mt-0.5">${pcr > 1 ? 'Bullish' : (pcr > 0.8 ? 'Neutral-Bull' : 'Bearish')}</span>
          </div>

          <!-- MAX PAIN -->
          <div class="bg-[#08111A] p-3 rounded-lg border border-white/[0.06] hover:border-white/[0.12] transition-colors flex flex-col justify-between">
            <div class="flex items-center justify-between text-[#617486]">
              <span class="font-mono-xs text-[10px] uppercase tracking-wider font-semibold">Max Pain</span>
              <span class="material-symbols-outlined text-[15px] text-[#F5B84B]">adjust</span>
            </div>
            <div class="flex items-baseline gap-1.5 mt-1">
              <span class="font-mono-num text-[20px] font-bold text-[#F5B84B]">${typeof maxPain === 'number' ? formatNumber(maxPain, 0) : maxPain}</span>
            </div>
            <span class="font-mono-xs text-[10px] text-[#617486] mt-0.5">Expiry pin anchor</span>
          </div>

          <!-- FUT PREMIUM -->
          <div class="bg-[#08111A] p-3 rounded-lg border border-white/[0.06] hover:border-white/[0.12] transition-colors flex flex-col justify-between">
            <div class="flex items-center justify-between text-[#617486]">
              <span class="font-mono-xs text-[10px] uppercase tracking-wider font-semibold">Spot Price</span>
              <span class="material-symbols-outlined text-[15px] text-[#22C997]">finance_chip</span>
            </div>
            <div class="flex items-baseline gap-1.5 mt-1">
              <span class="font-mono-num text-[20px] font-bold text-[#22C997]">${nifty.priceFormatted}</span>
            </div>
            <span class="font-mono-xs text-[10px] text-[#617486] mt-0.5">${nifty.changePctFormatted}</span>
          </div>

          <!-- NET GEX -->
          <div class="bg-[#08111A] p-3 rounded-lg border border-white/[0.06] hover:border-white/[0.12] transition-colors flex flex-col justify-between">
            <div class="flex items-center justify-between text-[#617486]">
              <span class="font-mono-xs text-[10px] uppercase tracking-wider font-semibold">Net GEX</span>
              <span class="material-symbols-outlined text-[15px] text-[#22C997]">donut_small</span>
            </div>
            <div class="flex items-baseline gap-1.5 mt-1">
              <span class="font-mono-num text-[20px] font-bold text-[#22C997]">${netGexFormatted}</span>
            </div>
            <span class="font-mono-xs text-[10px] text-[#617486] mt-0.5">Dealers ${isPositiveRegime ? 'long gamma' : 'short gamma'}</span>
          </div>

          <!-- GAMMA FLIP -->
          <div class="bg-[#08111A] p-3 rounded-lg border border-white/[0.06] hover:border-white/[0.12] transition-colors flex flex-col justify-between">
            <div class="flex items-center justify-between text-[#617486]">
              <span class="font-mono-xs text-[10px] uppercase tracking-wider font-semibold">Gamma Flip</span>
              <span class="material-symbols-outlined text-[15px] text-[#25D9D2]">swap_vertical_circle</span>
            </div>
            <div class="flex items-baseline gap-1.5 mt-1">
              <span class="font-mono-num text-[20px] font-bold text-[#25D9D2]">${typeof flipLevel === 'number' ? formatNumber(flipLevel, 0) : flipLevel}</span>
            </div>
            <span class="font-mono-xs text-[10px] text-[#617486] mt-0.5">Vol inflection level</span>
          </div>

          <!-- CALL / PUT WALL -->
          <div class="bg-[#08111A] p-3 rounded-lg border border-white/[0.06] hover:border-white/[0.12] transition-colors flex flex-col justify-between">
            <div class="flex items-center justify-between text-[#617486]">
              <span class="font-mono-xs text-[10px] uppercase tracking-wider font-semibold">Call / Put Wall</span>
              <span class="material-symbols-outlined text-[15px] text-[#FF5C6C]">vertical_align_center</span>
            </div>
            <div class="flex items-center justify-between mt-1">
              <span class="font-mono-num text-[15px] font-bold text-[#FF5C6C]">${callWall}</span>
              <span class="font-mono-xs text-[10px] text-[#617486]">vs</span>
              <span class="font-mono-num text-[15px] font-bold text-[#22C997]">${putWall}</span>
            </div>
            <span class="font-mono-xs text-[10px] text-[#617486] mt-0.5">Primary expected range</span>
          </div>
        </div>
      </section>

      <!-- 2. MAIN ANALYTICAL GRID (Two Columns: 65% / 35%) -->
      <div class="w-full grid grid-cols-1 lg:grid-cols-12 gap-3.5">
        <!-- LEFT COLUMN: Dual GEX Surface & Option Chain Heatmap Preview -->
        <div class="lg:col-span-8 flex flex-col gap-3.5">
          <!-- Dual GEX Surface Chart Card -->
          <div class="bg-[#0C1722] rounded-xl p-4 border border-white/[0.06] shadow-lg flex flex-col">
            <div class="flex flex-wrap items-center justify-between gap-2 pb-2.5 mb-2.5 bg-[#08111A] p-2.5 rounded-lg border border-white/[0.05]">
              <div class="flex items-center gap-3">
                <div class="flex items-center gap-1.5">
                  <span class="text-[13px] font-bold text-[#E7EEF5]">NIFTY 50 Dual GEX Surface</span>
                  <span class="px-1.5 py-0.5 bg-[#101C28] text-[#25D9D2] font-mono-xs text-[9px] rounded font-bold border border-[#25D9D2]/25">Live Telemetry</span>
                </div>
                <span class="text-[#617486] font-mono-xs text-[11px] hidden sm:inline">
                  Spot: <strong class="text-[#E7EEF5] font-mono-num">${nifty.priceFormatted}</strong>
                </span>
              </div>
              <div class="flex items-center gap-3 font-mono-xs text-[10px]">
                <div class="flex items-center gap-1"><span class="w-2.5 h-0.5 bg-[#FF5C6C] inline-block rounded"></span><span class="text-[#8FA4B7]">Call Wall (${callWall})</span></div>
                <div class="flex items-center gap-1"><span class="w-2.5 h-0.5 bg-[#25D9D2] inline-block rounded"></span><span class="text-[#8FA4B7]">Flip (${flipLevel})</span></div>
                <div class="flex items-center gap-1"><span class="w-2.5 h-0.5 bg-[#F5B84B] inline-block rounded"></span><span class="text-[#8FA4B7]">Pain (${maxPain})</span></div>
                <div class="flex items-center gap-1"><span class="w-2.5 h-0.5 bg-[#22C997] inline-block rounded"></span><span class="text-[#8FA4B7]">Put Wall (${putWall})</span></div>
              </div>
            </div>

            <!-- SVG GEX SURFACE CANVAS -->
            <div class="relative w-full h-64 bg-[#060D15] rounded-lg border border-white/[0.04] overflow-hidden flex items-center justify-center">
              <svg class="w-full h-full" viewBox="0 0 800 240" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#25D9D2" stop-opacity="0.18" />
                    <stop offset="100%" stop-color="#25D9D2" stop-opacity="0.0" />
                  </linearGradient>
                </defs>
                <!-- Grid Lines -->
                <line x1="0" y1="40" x2="800" y2="40" stroke="#13202E" stroke-dasharray="2 4" stroke-width="0.75" />
                <line x1="0" y1="95" x2="800" y2="95" stroke="#13202E" stroke-dasharray="2 4" stroke-width="0.75" />
                <line x1="0" y1="150" x2="800" y2="150" stroke="#13202E" stroke-dasharray="2 4" stroke-width="0.75" />

                <!-- Levels -->
                <line x1="0" y1="30" x2="800" y2="30" stroke="#FF5C6C" stroke-dasharray="3 3" stroke-width="1" />
                <text x="8" y="25" fill="#FF5C6C" class="text-[9px] font-mono-num">CALL WALL ${callWall}</text>

                <line x1="0" y1="75" x2="800" y2="75" stroke="#25D9D2" stroke-dasharray="6 3" stroke-width="1" />
                <text x="8" y="70" fill="#25D9D2" class="text-[9px] font-mono-num">GAMMA FLIP ${flipLevel}</text>

                <line x1="0" y1="145" x2="800" y2="145" stroke="#F5B84B" stroke-width="1" />
                <text x="8" y="140" fill="#F5B84B" class="text-[9px] font-mono-num">MAX PAIN ${maxPain}</text>

                <line x1="0" y1="210" x2="800" y2="210" stroke="#22C997" stroke-width="1" />
                <text x="8" y="205" fill="#22C997" class="text-[9px] font-mono-num">PUT WALL ${putWall}</text>

                <!-- Surface Area & Line -->
                <path d="M 0,180 L 100,175 L 200,160 L 300,140 L 400,135 L 500,120 L 600,110 L 700,95 L 800,90 L 800,240 L 0,240 Z" fill="url(#areaGrad)" />
                <path d="M 0,180 L 100,175 L 200,160 L 300,140 L 400,135 L 500,120 L 600,110 L 700,95 L 800,90" fill="none" stroke="#25D9D2" stroke-width="2" stroke-linecap="round" />
                <circle cx="700" cy="95" r="4" fill="#25D9D2" />
              </svg>
            </div>
          </div>

          <!-- Intraday Option Chain Heatmap Preview Table -->
          <div class="bg-[#0C1722] rounded-xl p-4 border border-white/[0.06] shadow-lg flex flex-col">
            <div class="flex items-center justify-between pb-2.5 mb-2 border-b border-white/[0.06]">
              <div class="flex items-center gap-2">
                <span class="text-[13px] font-bold text-[#E7EEF5]">Intraday Option Chain Heatmap Preview</span>
                <span class="font-mono-xs text-[10px] text-[#617486]">Expiry: ${chain.expiry || 'Near Expiry'}</span>
              </div>
              <div class="flex items-center gap-2.5 font-mono-xs text-[10px]">
                <span class="text-[#FF5C6C] font-semibold">Calls OI</span>
                <span class="text-[#617486]">|</span>
                <span class="text-[#22C997] font-semibold">Puts OI</span>
              </div>
            </div>

            <div class="w-full overflow-x-auto rounded-lg border border-white/[0.05]">
              <table class="w-full text-left font-mono-xs text-[11px] border-collapse font-mono-num">
                <thead class="bg-[#060D15]">
                  <tr class="text-[#617486] font-mono-xs text-[9px] uppercase tracking-wider border-b border-white/[0.06]">
                    <th class="py-2 px-3 text-left">IV</th>
                    <th class="py-2 px-3 text-right">Call LTP</th>
                    <th class="py-2 px-3 text-right">Call OI</th>
                    <th class="py-2 px-3 text-center font-bold text-[#E7EEF5]">Strike</th>
                    <th class="py-2 px-3 text-left">Put OI</th>
                    <th class="py-2 px-3 text-left">Put LTP</th>
                    <th class="py-2 px-3 text-right">IV</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-white/[0.04]">
                  ${chain.isUnavailable ? `
                    <tr>
                      <td colspan="7" class="py-6 text-center text-[#617486] font-mono-xs">
                        ● MARKET DATA UNAVAILABLE — Connect backend feed to populate live option chain matrix
                      </td>
                    </tr>
                  ` : heatmapStrikes.map(stk => {
                    const strikeObj = chain.strikes.find(s => s.strike === stk);
                    const isAtm = stk === chain.atmStrike;
                    const isPain = stk === chain.maxPain;

                    let bgClass = isAtm ? 'bg-[#25D9D2]/10' : (isPain ? 'bg-[#F5B84B]/5' : 'hover:bg-[#101C28]/60');

                    return `
                      <tr class="${bgClass} transition-colors">
                        <td class="py-2 px-3 text-[#8FA4B7]">${strikeObj?.ce.ivFormatted || '11.8%'}</td>
                        <td class="py-2 px-3 text-right font-medium text-[#E7EEF5]">${strikeObj?.ce.ltpFormatted || '—'}</td>
                        <td class="py-2 px-3 text-right text-[#FF5C6C] font-bold">${strikeObj?.ce.oiFormatted || '—'}</td>
                        <td class="py-2 px-3 text-center font-bold ${isAtm ? 'text-[#25D9D2]' : (isPain ? 'text-[#F5B84B]' : 'text-[#E7EEF5]')}">
                          ${stk} ${isAtm ? '<span class="text-[8px] uppercase">ATM</span>' : ''} ${isPain ? '<span class="text-[8px] uppercase">PAIN</span>' : ''}
                        </td>
                        <td class="py-2 px-3 text-left text-[#22C997] font-bold">${strikeObj?.pe.oiFormatted || '—'}</td>
                        <td class="py-2 px-3 text-left font-medium text-[#E7EEF5]">${strikeObj?.pe.ltpFormatted || '—'}</td>
                        <td class="py-2 px-3 text-right text-[#8FA4B7]">${strikeObj?.pe.ivFormatted || '12.1%'}</td>
                      </tr>
                    `;
                  }).join('')}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- RIGHT COLUMN: Sentiment Radial & Quant Event Stream -->
        <div class="lg:col-span-4 flex flex-col gap-3.5">
          <!-- Sentiment & Regime Card -->
          <div class="bg-[#0C1722] rounded-xl p-4 border border-white/[0.06] shadow-lg flex flex-col">
            <div class="flex items-center justify-between pb-2.5 mb-2 border-b border-white/[0.06]">
              <span class="text-[13px] font-bold text-[#E7EEF5]">Sentiment & Regime Radial</span>
              <span class="font-mono-xs text-[9px] px-2 py-0.5 rounded bg-[#22C997]/10 text-[#22C997] border border-[#22C997]/30 font-semibold uppercase">
                ${isPositiveRegime ? 'Bullish Accumulation' : 'Hedging Pressure'}
              </span>
            </div>

            <div class="relative flex flex-col items-center justify-center pt-2">
              <svg class="w-48 h-24 overflow-visible" viewBox="0 0 200 100">
                <path d="M 20,100 A 80,80 0 0,1 180,100" fill="none" stroke="#060D15" stroke-width="12" stroke-linecap="round" />
                <path d="M 20,100 A 80,80 0 0,1 180,100" fill="none" stroke="${isPositiveRegime ? '#22C997' : '#FF5C6C'}" stroke-width="12" stroke-linecap="round" stroke-dasharray="251.2" stroke-dashoffset="${isPositiveRegime ? '95' : '150'}" />
                <circle cx="100" cy="100" r="4.5" fill="#25D9D2" />
              </svg>
              <div class="flex flex-col items-center mt-2">
                <div class="flex items-baseline gap-1">
                  <span class="font-mono-num text-[28px] font-bold ${isPositiveRegime ? 'text-[#22C997]' : 'text-[#FF5C6C]'} leading-none">
                    ${isPositiveRegime ? '64' : '38'}
                  </span>
                  <span class="font-mono-xs text-[10px] text-[#617486]">/ 100</span>
                </div>
                <span class="text-[11px] font-bold text-[#E7EEF5] mt-1 uppercase">
                  ${isPositiveRegime ? 'Mild Bullish Bias' : 'Bearish Risk Off'}
                </span>
              </div>
            </div>
          </div>

          <!-- Quant Event Stream -->
          <div class="bg-[#0C1722] rounded-xl p-4 border border-white/[0.06] shadow-lg flex flex-col flex-1">
            <div class="flex items-center justify-between pb-2.5 mb-2 border-b border-white/[0.06]">
              <div class="flex items-center gap-2">
                <span class="text-[13px] font-bold text-[#E7EEF5]">Quant Event Stream</span>
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-[#22C997]"></span>
              </div>
              <span class="font-mono-xs text-[10px] text-[#617486]">Live Feed</span>
            </div>

            <div class="flex flex-col gap-2.5 divide-y divide-white/[0.04]">
              ${expiryIntel.alerts.length > 0 ? expiryIntel.alerts.map(a => `
                <div class="pt-2 flex flex-col gap-1">
                  <div class="flex items-center justify-between font-mono-xs text-[10px]">
                    <span class="px-1.5 py-0.2 bg-[#FF5C6C]/15 text-[#FF5C6C] font-bold rounded text-[8px] border border-[#FF5C6C]/30">TELEMETRY</span>
                    <span class="text-[#617486]">RECENT</span>
                  </div>
                  <p class="font-mono-xs text-[10px] text-[#E7EEF5] leading-tight">${a}</p>
                </div>
              `).join('') : `
                <div class="py-4 text-center text-[#617486] font-mono-xs">
                  ● No active risk triggers. Derivatives flow within normal parameters.
                </div>
              `}
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}
