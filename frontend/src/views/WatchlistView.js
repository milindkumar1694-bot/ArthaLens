import { adaptWatchlist, formatNumber } from '../adapters/index.js';

export function renderWatchlistView(rawWatchlistData) {
  const watchlist = adaptWatchlist(rawWatchlistData);

  return `
    <div class="flex flex-col w-full text-[#E7EEF5] pb-12 bg-[#05080D]">
      <!-- 1. HEADER CARD -->
      <section class="bg-[#0C1722] rounded-xl p-5 border border-white/[0.06] shadow-xl mb-5">
        <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 pb-3 border-b border-white/[0.06]">
          <div class="flex flex-col">
            <div class="flex items-center gap-2 font-mono-xs text-[11px] mb-1">
              <span class="material-symbols-outlined text-[16px] text-[#25D9D2]">candlestick_chart</span>
              <span class="text-[#25D9D2] font-semibold uppercase tracking-wider text-[10px]">Multi-Asset Priority Scanner</span>
            </div>
            <h1 class="text-[22px] font-bold tracking-tight text-[#E7EEF5]">Quantitative Watchlist & Trade Setup Ranking</h1>
          </div>

          <div class="flex items-center gap-2 flex-wrap">
            ${watchlist.universe.map(u => `
              <span class="px-2.5 py-1 bg-[#08111A] text-[#8FA4B7] border border-white/[0.06] font-mono-xs text-[10px] rounded font-semibold">
                ${u}
              </span>
            `).join('')}
          </div>
        </div>
      </section>

      <!-- 2. WATCHLIST SCANNER TABLE -->
      <div class="bg-[#0C1722] rounded-xl p-4 border border-white/[0.06] shadow-lg">
        <div class="flex items-center justify-between pb-3 mb-3 border-b border-white/[0.06]">
          <span class="text-[13px] font-bold text-[#E7EEF5]">Ranked Asset Drivers (${watchlist.items.length})</span>
          <span class="font-mono-xs text-[10px] text-[#617486]">Sorted by Priority Score</span>
        </div>

        ${watchlist.isUnavailable ? `
          <div class="p-12 text-center flex flex-col items-center justify-center text-[#617486] font-mono-xs">
            <span class="material-symbols-outlined text-[36px] mb-2 text-[#FF5C6C]">search_off</span>
            <span class="font-bold text-[14px] text-[#E7EEF5] uppercase tracking-wider">WATCHLIST FEED UNAVAILABLE</span>
            <p class="text-[11px] text-[#8FA4B7] mt-1 max-w-md leading-relaxed">
              Live market quotes required to calculate asset priority scores. Prototype scores are suppressed in production.
            </p>
          </div>
        ` : `
          <div class="w-full overflow-x-auto">
            <table class="w-full text-left font-mono-xs text-[11px] border-collapse">
              <thead class="bg-[#060D15]">
                <tr class="text-[#617486] uppercase tracking-wider border-b border-white/[0.06] font-mono-xs text-[9px]">
                  <th class="py-2.5 px-3 text-center">Rank</th>
                  <th class="py-2.5 px-3">Asset</th>
                  <th class="py-2.5 px-3">Catalyst Event</th>
                  <th class="py-2.5 px-3">Quantitative Reason</th>
                  <th class="py-2.5 px-3 text-center">Priority Score</th>
                  <th class="py-2.5 px-3 text-center">Direction</th>
                  <th class="py-2.5 px-3">Trade Hint</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/[0.04] font-mono-num">
                ${watchlist.items.map(item => {
                  const score = item.priorityScore ?? 50;
                  const isHigh = score >= 75;
                  const isMed = score >= 50 && score < 75;

                  const badgeClass = isHigh ? 'bg-[#FF5C6C]/20 text-[#FF5C6C] border-[#FF5C6C]/40' : (isMed ? 'bg-[#F5B84B]/20 text-[#F5B84B] border-[#F5B84B]/40' : 'bg-[#25D9D2]/20 text-[#25D9D2] border-[#25D9D2]/40');
                  const dirColor = item.direction === 'Positive' ? 'text-[#22C997]' : (item.direction === 'Negative' ? 'text-[#FF5C6C]' : 'text-[#8FA4B7]');

                  return `
                    <tr class="hover:bg-[#101C28]/60 transition-colors">
                      <td class="py-3 px-3 text-center font-bold text-[#617486]">#${item.rank}</td>
                      <td class="py-3 px-3 font-bold text-[#E7EEF5]">${item.asset}</td>
                      <td class="py-3 px-3 text-[#25D9D2] font-semibold">${item.eventOrDriver}</td>
                      <td class="py-3 px-3 text-[#8FA4B7] max-w-xs leading-tight">${item.reason}</td>
                      <td class="py-3 px-3 text-center">
                        <span class="px-2.5 py-1 rounded border font-bold text-[12px] ${badgeClass}">
                          ${formatNumber(score, 1)}
                        </span>
                      </td>
                      <td class="py-3 px-3 text-center font-bold ${dirColor}">${item.direction}</td>
                      <td class="py-3 px-3 text-[#E7EEF5] bg-[#08111A]/50 font-medium">${item.tradeHint}</td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>
        `}
      </div>
    </div>
  `;
}
