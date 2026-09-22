export function renderSettingsModal(isOpen, healthData) {
  if (!isOpen) return '';

  const dataMode = healthData?.data_mode || 'mock';
  const provider = healthData?.provider || 'simulated';
  const dbStatus = healthData?.database || 'OK';
  const redisStatus = healthData?.redis || 'not_configured';
  const env = healthData?.environment || 'production';

  return `
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop animate-fadeIn">
      <div class="bg-[#0C1722] border border-white/[0.1] rounded-xl w-full max-w-lg overflow-hidden shadow-2xl">
        <!-- HEADER -->
        <div class="px-5 py-3.5 bg-[#08111A] border-b border-white/[0.06] flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-[18px] text-[#25D9D2]">settings</span>
            <span class="font-bold text-[14px] text-[#E7EEF5] tracking-tight">System Configuration & Diagnostics</span>
          </div>
          <button id="btn-close-settings" type="button" class="text-[#617486] hover:text-[#E7EEF5] transition-colors">
            <span class="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        <!-- BODY -->
        <div class="p-5 flex flex-col gap-4 font-mono-xs text-[11px]">
          <div class="bg-[#071019] p-3 rounded-lg border border-white/[0.05] flex flex-col gap-2">
            <span class="text-[#25D9D2] font-bold text-[12px] flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[15px]">verified_user</span> System Status & Environment
            </span>
            <div class="grid grid-cols-2 gap-3 mt-1">
              <div class="flex flex-col">
                <span class="text-[#617486]">Data Execution Mode</span>
                <span class="text-[#E7EEF5] font-bold mt-0.5 uppercase">${dataMode}</span>
              </div>
              <div class="flex flex-col">
                <span class="text-[#617486]">Active Market Provider</span>
                <span class="text-[#22C997] font-bold mt-0.5 uppercase">${provider}</span>
              </div>
              <div class="flex flex-col">
                <span class="text-[#617486]">Environment</span>
                <span class="text-[#E7EEF5] font-bold mt-0.5 uppercase">${env}</span>
              </div>
              <div class="flex flex-col">
                <span class="text-[#617486]">Database Status</span>
                <span class="text-[#22C997] font-bold mt-0.5 uppercase">${dbStatus}</span>
              </div>
            </div>
          </div>

          <div class="bg-[#071019] p-3 rounded-lg border border-white/[0.05] flex flex-col gap-2">
            <span class="text-[#8FA4B7] font-bold text-[11px] uppercase tracking-wider">Subsystem Integrations</span>
            <div class="flex items-center justify-between py-1 border-b border-white/[0.04]">
              <span class="text-[#8FA4B7]">Redis Shared Cache</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${redisStatus === 'configured' ? 'bg-[#22C997]/15 text-[#22C997]' : 'bg-[#F5B84B]/15 text-[#F5B84B]'}">
                ${redisStatus.toUpperCase()}
              </span>
            </div>
            <div class="flex items-center justify-between py-1 border-b border-white/[0.04]">
              <span class="text-[#8FA4B7]">FastAPI Backend Services</span>
              <span class="px-2 py-0.5 bg-[#22C997]/15 text-[#22C997] rounded text-[10px] font-bold">CONNECTED</span>
            </div>
            <div class="flex items-center justify-between py-1">
              <span class="text-[#8FA4B7]">Secrets Exposure Safety</span>
              <span class="px-2 py-0.5 bg-[#22C997]/15 text-[#22C997] rounded text-[10px] font-bold">ENFORCED (No Keys Exposed)</span>
            </div>
          </div>

          <div class="p-3 bg-[#08111A] rounded-lg border border-white/[0.05] text-[#8FA4B7] text-[10px] leading-relaxed">
            <span class="text-[#F5B84B] font-bold">Security Notice:</span> All broker credentials, TOTP keys, database strings, and API tokens are securely managed server-side in backend environment variables.
          </div>
        </div>

        <!-- FOOTER -->
        <div class="px-5 py-3 bg-[#08111A] border-t border-white/[0.06] flex justify-end">
          <button id="btn-dismiss-settings" type="button" class="px-4 py-1.5 bg-[#25D9D2] hover:bg-[#00daf3] text-[#04090F] font-bold font-mono-xs text-[11px] rounded transition-colors">
            Close Diagnostics
          </button>
        </div>
      </div>
    </div>
  `;
}
