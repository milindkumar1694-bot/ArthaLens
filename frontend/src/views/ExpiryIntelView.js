import { adaptExpiryIntel, formatNumber, formatLakhs } from '../adapters/index.js';

export function renderExpiryIntelView(rawIntelData, activeSymbol = 'NIFTY') {
  const intel = adaptExpiryIntel(rawIntelData);

  return `
    <div class="flex flex-col w-full text-[#E7EEF5] pb-12 bg-[#05080D]">
      <!-- 1. TOP HEADER SUMMARY CARD -->
      <section class="bg-[#0C1722] rounded-xl p-5 border border-white/[0.06] shadow-xl mb-5">
        <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
          <div class="flex flex-col">
            <div class="flex items-center gap-2 font-mono-xs text-[11px] mb-1">
              <span class="material-symbols-outlined text-[16px] text-[#25D9D2]">analytics</span>
              <span class="text-[#25D9D2] font-semibold uppercase tracking-wider text-[10px]">Expiry Intelligence Desk</span>
              <span class="text-[#617486]">| Symbol: ${activeSymbol}</span>
            </div>
            <h1 class="text-[22px] font-bold tracking-tight text-[#E7EEF5]">Gamma Exposure (GEX) & Expiry Regime</h1>
          </div>

          <div class="flex items-center gap-3">
            <div class="bg-[#071019] px-3.5 py-1.5 rounded-lg border border-white/[0.06] flex items-center gap-2">
              <span class="font-mono-xs text-[10px] text-[#617486] uppercase">EXPIRY:</span>
              <span class="font-mono-num text-[12px] font-bold text-[#25D9D2]">${intel.expiry || 'CURRENT'}</span>
            </div>
          </div>
        </div>

        <!-- METRICS TILES -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 pt-4 font-mono-xs text-[11px]">
          <div class="bg-[#08111A] p-3 rounded-lg border border-white/[0.06]">
            <span class="text-[#617486] uppercase font-semibold text-[10px]">Net GEX Regime</span>
            <div class="font-mono-num text-[18px] font-bold ${intel.netGex >= 0 ? 'text-[#22C997]' : 'text-[#FF5C6C]'} mt-1">
              ${intel.regime}
            </div>
            <span class="text-[#8FA4B7] text-[10px]">${intel.netGexFormatted} Total GEX</span>
          </div>

          <div class="bg-[#08111A] p-3 rounded-lg border border-white/[0.06]">
            <span class="text-[#617486] uppercase font-semibold text-[10px]">Pin Target Strike</span>
            <div class="font-mono-num text-[18px] font-bold text-[#F5B84B] mt-1">
              ${intel.pinTarget ? formatNumber(intel.pinTarget, 0) : '—'}
            </div>
            <span class="text-[#8FA4B7] text-[10px]">Maximum OI Pain Center</span>
          </div>

          <div class="bg-[#08111A] p-3 rounded-lg border border-white/[0.06]">
            <span class="text-[#617486] uppercase font-semibold text-[10px]">Violence Risk</span>
            <div class="font-mono-num text-[18px] font-bold ${intel.violenceProbability === 'HIGH' ? 'text-[#FF5C6C]' : 'text-[#22C997]'} mt-1">
              ${intel.violenceProbability}
            </div>
            <span class="text-[#8FA4B7] text-[10px]">Breakout / Squeeze potential</span>
          </div>

          <div class="bg-[#08111A] p-3 rounded-lg border border-white/[0.06]">
            <span class="text-[#617486] uppercase font-semibold text-[10px]">Dealer Positioning</span>
            <div class="font-mono-num text-[18px] font-bold text-[#25D9D2] mt-1">
              ${intel.dealerHedging?.dealer_position || 'Neutral'}
            </div>
            <span class="text-[#8FA4B7] text-[10px]">${intel.dealerHedging?.hedging_direction || '—'}</span>
          </div>
        </div>
      </section>

      <!-- 2. ANALYTICS & PROBABILITY CARDS GRID -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-3.5 mb-5">
        <!-- Dealer Hedging Estimate Card -->
        <div class="lg:col-span-6 bg-[#0C1722] rounded-xl p-4 border border-white/[0.06] shadow-lg flex flex-col justify-between">
          <div class="flex items-center justify-between pb-2 mb-3 border-b border-white/[0.06]">
            <span class="text-[13px] font-bold text-[#E7EEF5]">Dealer Hedging Dynamics</span>
            <span class="font-mono-xs text-[9px] px-2 py-0.5 rounded bg-[#25D9D2]/10 text-[#25D9D2] font-semibold uppercase">Quantitative Estimate</span>
          </div>

          <div class="flex flex-col gap-2.5 font-mono-xs text-[11px]">
            <div class="flex items-center justify-between py-1 border-b border-white/[0.04]">
              <span class="text-[#8FA4B7]">Gamma Flip Level</span>
              <span class="font-bold text-[#25D9D2] font-mono-num">
                ${intel.dealerHedging?.gamma_flip_level ? formatNumber(intel.dealerHedging.gamma_flip_level, 0) : '—'}
              </span>
            </div>
            <div class="flex items-center justify-between py-1 border-b border-white/[0.04]">
              <span class="text-[#8FA4B7]">Distance to Flip Level</span>
              <span class="font-bold text-[#E7EEF5] font-mono-num">
                ${intel.dealerHedging?.distance_to_flip !== null && intel.dealerHedging?.distance_to_flip !== undefined ? `${intel.dealerHedging.distance_to_flip} pts` : '—'}
              </span>
            </div>
            <div class="flex items-center justify-between py-1 border-b border-white/[0.04]">
              <span class="text-[#8FA4B7]">Hedging Action</span>
              <span class="font-bold text-[#22C997]">${intel.dealerHedging?.hedging_direction || '—'}</span>
            </div>
          </div>
        </div>

        <!-- Expiry Probability Score Card -->
        <div class="lg:col-span-6 bg-[#0C1722] rounded-xl p-4 border border-white/[0.06] shadow-lg flex flex-col justify-between">
          <div class="flex items-center justify-between pb-2 mb-3 border-b border-white/[0.06]">
            <span class="text-[13px] font-bold text-[#E7EEF5]">Expiry Probability Breakdown</span>
            <span class="font-mono-xs text-[9px] px-2 py-0.5 rounded bg-[#22C997]/10 text-[#22C997] font-semibold uppercase">Distribution</span>
          </div>

          <div class="flex flex-col gap-3 font-mono-xs text-[11px]">
            <div>
              <div class="flex items-center justify-between text-[#8FA4B7] mb-1">
                <span>Pinning Probability</span>
                <span class="font-bold text-[#22C997]">${intel.probabilityScore?.pinning_probability || 33}%</span>
              </div>
              <div class="w-full h-2 bg-[#071019] rounded overflow-hidden">
                <div class="h-full bg-[#22C997]" style="width: ${intel.probabilityScore?.pinning_probability || 33}%"></div>
              </div>
            </div>

            <div>
              <div class="flex items-center justify-between text-[#8FA4B7] mb-1">
                <span>Gamma Squeeze Probability</span>
                <span class="font-bold text-[#FF5C6C]">${intel.probabilityScore?.squeeze_probability || 33}%</span>
              </div>
              <div class="w-full h-2 bg-[#071019] rounded overflow-hidden">
                <div class="h-full bg-[#FF5C6C]" style="width: ${intel.probabilityScore?.squeeze_probability || 33}%"></div>
              </div>
            </div>

            <p class="text-[10px] text-[#617486] leading-relaxed pt-1">
              Primary Factor: ${intel.probabilityScore?.primary_factor || 'Balanced option interest across strikes.'}
            </p>
          </div>
        </div>
      </div>

      <!-- 3. HISTORICAL EXPIRY PATTERNS (Requirements Section #11) -->
      <section class="bg-[#0C1722] rounded-xl p-5 border border-white/[0.06] shadow-xl">
        <div class="flex items-center justify-between pb-3 mb-3 border-b border-white/[0.06]">
          <span class="text-[13px] font-bold text-[#E7EEF5]">Historical Expiry Comparison</span>
          <span class="font-mono-xs text-[9px] px-2 py-0.5 rounded bg-[#071019] text-[#8FA4B7] border border-white/[0.06]">
            Historical Backtest Record
          </span>
        </div>

        ${!intel.hasHistory ? `
          <div class="p-8 text-center flex flex-col items-center justify-center text-[#617486] font-mono-xs">
            <span class="material-symbols-outlined text-[32px] mb-2 text-[#F5B84B]">history_toggle_off</span>
            <span class="font-bold text-[13px] text-[#E7EEF5] uppercase tracking-wider">INSUFFICIENT HISTORICAL DATA</span>
            <p class="text-[11px] text-[#8FA4B7] mt-1 max-w-md leading-relaxed">
              Historical backtest records for this specific contract are unavailable in live market mode. Prototype data is strictly suppressed in production.
            </p>
          </div>
        ` : `
          <div class="w-full overflow-x-auto">
            <table class="w-full text-left font-mono-xs text-[11px] border-collapse font-mono-num">
              <thead class="bg-[#060D15]">
                <tr class="text-[#617486] uppercase tracking-wider border-b border-white/[0.06]">
                  <th class="py-2.5 px-3">Date</th>
                  <th class="py-2.5 px-3">Symbol</th>
                  <th class="py-2.5 px-3">Regime</th>
                  <th class="py-2.5 px-3 text-right">Max Move (pts)</th>
                  <th class="py-2.5 px-3 text-right">Max Move (%)</th>
                  <th class="py-2.5 px-3 text-center">Pin Target Hit</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/[0.04]">
                ${intel.historicalComparison.map(h => `
                  <tr class="hover:bg-[#101C28]/60 transition-colors">
                    <td class="py-2 px-3 text-[#E7EEF5] font-bold">${h.date}</td>
                    <td class="py-2 px-3 text-[#25D9D2]">${h.symbol}</td>
                    <td class="py-2 px-3 text-[#8FA4B7]">${h.net_gex_regime}</td>
                    <td class="py-2 px-3 text-right font-medium text-[#E7EEF5]">${h.max_intraday_move_pts}</td>
                    <td class="py-2 px-3 text-right text-[#22C997]">${h.max_intraday_move_pct}%</td>
                    <td class="py-2 px-3 text-center">
                      <span class="px-2 py-0.5 rounded text-[9px] font-bold ${h.pin_target_hit ? 'bg-[#22C997]/15 text-[#22C997]' : 'bg-[#FF5C6C]/15 text-[#FF5C6C]'}">
                        ${h.pin_target_hit ? 'YES' : 'NO'}
                      </span>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        `}
      </section>
    </div>
  `;
}
