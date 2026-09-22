import { apiGet } from './client.js';

export function getNewsIntel(symbol = 'NIFTY') {
  return apiGet(`/news?symbol=${symbol}`);
}
