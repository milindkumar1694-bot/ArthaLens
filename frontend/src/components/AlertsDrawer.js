export function renderAlertsDrawer(isOpen, alertsList) {
  const translateClass = isOpen ? 'translate-x-0' : 'translate-x-full';
  const alerts = Array.isArray(alertsList) ? alertsList : [];

  return `
    <div id="alerts-drawer" class="fixed top-24 right-0 bottom-0 w-80 bg-[#071019] border-l border-white/[0.06] z-50 transform ${translateClass} transition-transform duration-200 flex flex-col shadow-2xl select-none">
      <div class="h-10 px-4 border-b border-white/[0.06] bg-[#060D15] flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-[16px] text-[#25D9D2]">notifications_active</span>
          <span class="font-mono-xs text-[10px] font-bold tracking-wider text-[#E7EEF5] uppercase">Real-Time Volatility Alerts</span>
        </div>
        <button id="btn-close-alerts" type="button" class="text-[#617486] hover:text-[#E7EEF5] transition-colors">
          <span class="material-symbols-outlined text-[16px]">close</span>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto divide-y divide-white/[0.04]">
        ${alerts.length === 0 ? `
          <div class="p-6 text-center flex flex-col items-center justify-center h-48 text-[#617486]">
            <span class="material-symbols-outlined text-[32px] mb-2 text-[#25D9D2]">shield</span>
            <span class="font-bold text-[12px] text-[#E7EEF5]">All Parameters Nominal</span>
            <p class="font-mono-xs text-[10px] text-[#8FA4B7] mt-1 max-w-xs leading-relaxed">
              No active volatility breaches or Gamma Wall tests detected.
            </p>
          </div>
        ` : alerts.map(item => {
          const isCritical = item.level === 'CRITICAL';
          const isHigh = item.level === 'HIGH';
          const border = isCritical ? 'border-l-2 border-[#FF5C6C] bg-[#FF5C6C]/[0.05]' : (isHigh ? 'border-l-2 border-[#F5B84B] bg-[#F5B84B]/[0.05]' : 'border-l-2 border-[#25D9D2] bg-[#25D9D2]/[0.05]');
          const tagBg = isCritical ? 'bg-[#FF5C6C]/20 text-[#FF5C6C]' : (isHigh ? 'bg-[#F5B84B]/20 text-[#F5B84B]' : 'bg-[#25D9D2]/20 text-[#25D9D2]');

          return `
            <div class="p-3.5 ${border}">
              <div class="flex items-center justify-between mb-1">
                <span class="font-mono-xs text-[8px] px-1.5 py-0.2 rounded font-bold uppercase ${tagBg}">
                  ${item.level || 'INFO'}
                </span>
                <span class="font-mono-xs text-[9px] text-[#617486]">${item.time || 'JUST NOW'}</span>
              </div>
              <p class="text-[11px] text-[#E7EEF5] font-semibold">${item.title}</p>
              <p class="font-mono-xs text-[10px] text-[#8FA4B7] mt-0.5 leading-tight">${item.desc}</p>
            </div>
          `;
        }).join('')}
      </div>

      <div class="p-3 border-t border-white/[0.06] bg-[#060D15] text-center">
        <button id="btn-ack-alerts" type="button" class="w-full py-1.5 bg-[#0C1722] hover:bg-[#101C28] border border-white/[0.08] font-mono-xs text-[10px] text-[#8FA4B7] hover:text-[#E7EEF5] uppercase tracking-wider font-semibold rounded transition-colors">
          Acknowledge Telemetry
        </button>
      </div>
    </div>
  `;
}
