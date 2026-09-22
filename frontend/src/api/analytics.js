import { apiGet } from './client.js';

export function getAnalytics(symbol, expiry = null) {
  const query = expiry ? `?p_expiry=${expiry}` : '';
  return apiGet(`/analytics/${symbol}${query}`);
}
