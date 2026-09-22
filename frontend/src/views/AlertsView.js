export function renderAlertsView(rawAlertsData, activeFilter = 'ALL') {
  const alerts = Array.isArray(rawAlertsData) ? rawAlertsData : [];

  const filteredAlerts = alerts.filter(a => {
    if (activeFilter === 'CRITICAL') return a.level === 'CRITICAL';
    if (activeFilter === 'HIGH') return a.level === 'HIGH';
    if (activeFilter === 'MEDIUM') return a.level === 'MEDIUM';
    return true;
  });

  return `
    <div class="flex flex-col w-full text-[#E7EEF5] pb-12 bg-[#05080D]">
      <!-- 1. HEADER CARD -->
      <section class="bg-[#0C1722] rounded-xl p-5 border border-white/[0.06] shadow-xl mb-5">
        <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 pb-3 border-b border-white/[0.06]">
          <div class="flex flex-col">
            <div class="flex items-center gap-2 font-mono-xs text-[11px] mb-1">
              <span class="material-symbols-outlined text-[16px] text-[#25D9D2]">notifications_active</span>
              <span class="text-[#25D9D2] font-semibold uppercase tracking-wider text-[10px]">Real-Time Volatility Engine</span>
            </div>
            <h1 class="text-[22px] font-bold tracking-tight text-[#E7EEF5]">Quantitative & Derivatives Alerts Terminal</h1>
          </div>

          <!-- SEVERITY FILTERS -->
          <div class="flex items-center gap-1 bg-[#071019] p-1 rounded-lg border border-white/[0.06] font-mono-xs text-[10px]">
            <button data-alert-filter="ALL" class="px-3 py-1 rounded font-bold transition-colors ${activeFilter === 'ALL' ? 'bg-[#25D9D2] text-[#04090F]' : 'text-[#8FA4B7] hover:text-[#E7EEF5]'}">
              ALL (${alerts.length})
            </button>
            <button data-alert-filter="CRITICAL" class="px-3 py-1 rounded font-bold transition-colors ${activeFilter === 'CRITICAL' ? 'bg-[#FF5C6C] text-white' : 'text-[#FF5C6C] hover:bg-[#FF5C6C]/10'}">
              CRITICAL
            </button>
            <button data-alert-filter="HIGH" class="px-3 py-1 rounded font-bold transition-colors ${activeFilter === 'HIGH' ? 'bg-[#F5B84B] text-[#04090F]' : 'text-[#F5B84B] hover:bg-[#F5B84B]/10'}">
              HIGH
            </button>
          </div>
        </div>
      </section>

      <!-- 2. ALERTS FEED TABLE -->
      <div class="bg-[#0C1722] rounded-xl p-4 border border-white/[0.06] shadow-lg">
        <div class="flex items-center justify-between pb-3 mb-3 border-b border-white/[0.06]">
          <span class="text-[13px] font-bold text-[#E7EEF5]">System Risk Telemetry Feed (${filteredAlerts.length})</span>
          <span class="font-mono-xs text-[10px] text-[#617486]">Auto-Refresh Active</span>
        </div>

        ${filteredAlerts.length === 0 ? `
          <div class="p-12 text-center flex flex-col items-center justify-center text-[#617486] font-mono-xs">
            <span class="material-symbols-outlined text-[40px] mb-2 text-[#22C997]">verified_user</span>
            <span class="font-bold text-[14px] text-[#E7EEF5] uppercase tracking-wider">NO ACTIVE ALERTS DETECTED</span>
            <p class="text-[11px] text-[#8FA4B7] mt-1 max-w-md leading-relaxed">
              All derivative risk parameters, CAS windows, and Gamma Wall boundaries are operating within normal limits.
            </p>
          </div>
        ` : `
          <div class="w-full overflow-x-auto">
            <table class="w-full text-left font-mono-xs text-[11px] border-collapse">
              <thead class="bg-[#060D15]">
                <tr class="text-[#617486] uppercase tracking-wider border-b border-white/[0.06] font-mono-xs text-[9px]">
                  <th class="py-2.5 px-3">Severity</th>
                  <th class="py-2.5 px-3">Timestamp</th>
                  <th class="py-2.5 px-3">Instrument</th>
                  <th class="py-2.5 px-3">Trigger Condition</th>
                  <th class="py-2.5 px-3">Observed Value</th>
                  <th class="py-2.5 px-3">Threshold Level</th>
                  <th class="py-2.5 px-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/[0.04] font-mono-num">
                ${filteredAlerts.map(alert => {
                  const isCritical = alert.level === 'CRITICAL';
                  const isHigh = alert.level === 'HIGH';
                  const badgeClass = isCritical ? 'bg-[#FF5C6C]/20 text-[#FF5C6C] border-[#FF5C6C]/40' : (isHigh ? 'bg-[#F5B84B]/20 text-[#F5B84B] border-[#F5B84B]/40' : 'bg-[#25D9D2]/20 text-[#25D9D2] border-[#25D9D2]/40');

                  return `
                    <tr class="hover:bg-[#101C28]/60 transition-colors">
                      <td class="py-3 px-3">
                        <span class="px-2 py-0.5 rounded border font-bold text-[9px] uppercase ${badgeClass}">
                          ${alert.level}
                        </span>
                      </td>
                      <td class="py-3 px-3 text-[#617486]">${alert.time || '15:20:04 IST'}</td>
                      <td class="py-3 px-3 font-bold text-[#E7EEF5]">${alert.instrument || 'NIFTY 50'}</td>
                      <td class="py-3 px-3 text-[#25D9D2] font-semibold">${alert.title}</td>
                      <td class="py-3 px-3 text-[#FF5C6C] font-bold">${alert.observed || '—'}</td>
                      <td class="py-3 px-3 text-[#8FA4B7]">${alert.threshold || '—'}</td>
                      <td class="py-3 px-3 text-center">
                        <span class="px-2 py-0.5 rounded bg-[#22C997]/15 text-[#22C997] font-bold text-[9px]">
                          ACTIVE
                        </span>
                      </td>
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
