import { adaptNewsIntel } from '../adapters/index.js';

export function renderNewsIntelView(rawNewsData, activeSymbol = 'NIFTY') {
  const news = adaptNewsIntel(rawNewsData);

  return `
    <div class="flex flex-col w-full text-[#E7EEF5] pb-12 bg-[#05080D]">
      <!-- 1. HEADER CARD -->
      <section class="bg-[#0C1722] rounded-xl p-5 border border-white/[0.06] shadow-xl mb-5">
        <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 pb-3 border-b border-white/[0.06]">
          <div class="flex flex-col">
            <div class="flex items-center gap-2 font-mono-xs text-[11px] mb-1">
              <span class="material-symbols-outlined text-[16px] text-[#25D9D2]">newspaper</span>
              <span class="text-[#25D9D2] font-semibold uppercase tracking-wider text-[10px]">News & Sentiment Intelligence</span>
              <span class="text-[#617486]">| Symbol: ${activeSymbol}</span>
            </div>
            <h1 class="text-[22px] font-bold tracking-tight text-[#E7EEF5]">Real-Time Financial News & Options AI Fusion</h1>
          </div>

          <div class="flex items-center gap-3 font-mono-xs text-[11px]">
            <div class="bg-[#071019] px-3.5 py-1.5 rounded-lg border border-white/[0.06] flex items-center gap-2">
              <span class="text-[#617486] uppercase">AI FUSION SIGNAL:</span>
              <span class="font-bold text-[#22C997]">${news.fusionSignal ? news.fusionSignal.sentiment : 'NEUTRAL'}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 2. NEWS FEED CONTENT -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-3.5">
        <!-- Main News Feed -->
        <div class="lg:col-span-8 flex flex-col gap-3">
          <div class="bg-[#0C1722] rounded-xl p-4 border border-white/[0.06] shadow-lg flex flex-col">
            <div class="flex items-center justify-between pb-3 mb-3 border-b border-white/[0.06]">
              <span class="text-[13px] font-bold text-[#E7EEF5]">Market Headlines Feed</span>
              <span class="font-mono-xs text-[10px] text-[#617486]">${news.newsItems.length} Articles</span>
            </div>

            ${news.isUnavailable ? `
              <div class="p-12 text-center flex flex-col items-center justify-center text-[#617486] font-mono-xs">
                <span class="material-symbols-outlined text-[36px] mb-2 text-[#FF5C6C]">rss_feed_off</span>
                <span class="font-bold text-[14px] text-[#E7EEF5] uppercase tracking-wider">NEWS FEED UNAVAILABLE</span>
                <p class="text-[11px] text-[#8FA4B7] mt-1 max-w-md leading-relaxed">
                  Live market news feed is currently unconfigured or unavailable from external providers. Demo headlines are suppressed.
                </p>
              </div>
            ` : `
              <div class="flex flex-col gap-3 divide-y divide-white/[0.04]">
                ${news.newsItems.map(item => {
                  const isHigh = item.impact === 'HIGH';
                  const isMed = item.impact === 'MEDIUM';
                  const tagBg = isHigh ? 'bg-[#FF5C6C]/15 text-[#FF5C6C] border-[#FF5C6C]/30' : (isMed ? 'bg-[#F5B84B]/15 text-[#F5B84B] border-[#F5B84B]/30' : 'bg-[#101C28] text-[#8FA4B7] border-white/[0.06]');

                  return `
                    <div class="pt-3 flex flex-col gap-1.5">
                      <div class="flex items-center justify-between font-mono-xs text-[10px]">
                        <div class="flex items-center gap-2">
                          <span class="px-2 py-0.5 rounded font-bold uppercase border ${tagBg}">${item.category}</span>
                          <span class="text-[#8FA4B7] font-semibold">${item.source}</span>
                        </div>
                        <span class="text-[#617486]">${item.timestamp}</span>
                      </div>

                      <a href="${item.url}" target="_blank" class="text-[13px] font-bold text-[#E7EEF5] hover:text-[#25D9D2] transition-colors leading-snug">
                        ${item.title}
                      </a>

                      ${item.summary ? `<p class="font-mono-xs text-[11px] text-[#8FA4B7] leading-relaxed">${item.summary}</p>` : ''}

                      <div class="flex items-center gap-4 pt-1 font-mono-xs text-[10px] text-[#617486]">
                        <span>Relevance: <strong class="text-[#25D9D2]">${item.relevanceScore}%</strong></span>
                        <span>Impact Score: <strong class="${isHigh ? 'text-[#FF5C6C]' : 'text-[#22C997]'}">${item.impact}</strong></span>
                      </div>
                    </div>
                  `;
                }).join('')}
              </div>
            `}
          </div>
        </div>

        <!-- AI Fusion Summary Sidebar -->
        <div class="lg:col-span-4 flex flex-col gap-3">
          <div class="bg-[#0C1722] rounded-xl p-4 border border-white/[0.06] shadow-lg flex flex-col">
            <div class="flex items-center justify-between pb-2.5 mb-3 border-b border-white/[0.06]">
              <span class="text-[13px] font-bold text-[#E7EEF5]">AI Sentiment & Options Fusion</span>
              <span class="material-symbols-outlined text-[18px] text-[#25D9D2]">psychology</span>
            </div>

            <div class="p-3.5 bg-[#08111A] rounded-lg border border-white/[0.05] font-mono-xs text-[11px] leading-relaxed text-[#8FA4B7]">
              ${news.fusionSignal ? `
                <div class="flex flex-col gap-2">
                  <span class="text-[#25D9D2] font-bold text-[12px]">Quantitative Intelligence Synthesis</span>
                  <p class="text-[#E7EEF5]">${news.fusionSignal.summary || 'Options flow divergence aligned with macro sentiment.'}</p>
                </div>
              ` : `
                <p class="text-[#617486]">AI sentiment fusion model waiting for live news stream data.</p>
              `}
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}
