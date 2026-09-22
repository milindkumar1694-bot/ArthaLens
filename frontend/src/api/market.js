import { apiGet } from './client.js';
export const getHealth = () => apiGet('/health');
export const getMarketSnapshot = (symbol) => apiGet(`/market/${symbol}`);
export const getMarketBar = () => Promise.all(['NIFTY', 'BANKNIFTY', 'SENSEX', 'INDIAVIX'].map(getMarketSnapshot));
