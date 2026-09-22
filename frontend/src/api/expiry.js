import { apiGet } from './client.js';

export function getExpiryIntel(symbol, expiry = null) {
  const query = expiry ? `?expiry=${expiry}` : '';
  return apiGet(`/expiry/${symbol}${query}`);
}
