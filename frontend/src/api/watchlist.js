import { apiGet } from './client.js';

export function getWatchlist() {
  return apiGet('/watchlist');
}
