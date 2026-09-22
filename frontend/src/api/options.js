import { apiGet } from './client.js';
export const getExpiries = symbol => apiGet(`/options/expiries?symbol=${symbol}`);
export const getOptionChain = (symbol, expiry) => apiGet(`/options/${symbol}${expiry ? `?expiry=${encodeURIComponent(expiry)}` : ''}`);
