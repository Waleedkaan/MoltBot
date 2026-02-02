/**
 * API Service
 * Handles all backend API calls
 */
import axios from 'axios';

// Initial values - can be overridden by localStorage
const getInitialBaseUrl = () => {
    const saved = localStorage.getItem('MOLTBOT_API_URL');
    if (saved) return saved;
    return import.meta.env.VITE_API_URL || 'http://localhost:8000';
};

let API_BASE_URL = getInitialBaseUrl();

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Function to update base URL without page reload (for temporary or persistent changes)
export const updateBaseUrl = (newUrl) => {
    if (!newUrl) return;
    API_BASE_URL = newUrl;
    api.defaults.baseURL = newUrl;
    localStorage.setItem('MOLTBOT_API_URL', newUrl);
};

// WebSocket URL helper
export const getWsUrl = () => {
    const baseUrl = API_BASE_URL.replace('http', 'ws');
    return `${baseUrl}/ws/market`;
};

// ──────────────────────────────────────
// CONFIG & COINS
// ──────────────────────────────────────

export const getCoins = async () => {
    const response = await api.get('/api/coins');
    return response.data.coins;
};

export const getTimeframes = async () => {
    const response = await api.get('/api/timeframes');
    return response.data.timeframes;
};

export const getConfig = async () => {
    const response = await api.get('/api/config');
    return response.data;
};

// ──────────────────────────────────────
// MARKET DATA
// ──────────────────────────────────────

export const getMarketData = async (coin, timeframe, limit = 100) => {
    const response = await api.get(`/api/market-data/${coin}/${timeframe}`, {
        params: { limit }
    });
    return response.data;
};

export const getCurrentPrice = async (coin) => {
    const response = await api.get(`/api/current-price/${coin}`);
    return response.data;
};

// ──────────────────────────────────────
// PREDICTIONS
// ──────────────────────────────────────

export const getPrediction = async (coin, timeframe, minConfidence = 60) => {
    const response = await api.get(`/api/prediction/${coin}/${timeframe}`, {
        params: { min_confidence: minConfidence }
    });
    return response.data;
};

// ──────────────────────────────────────
// USER SETTINGS
// ──────────────────────────────────────

export const getUserSettings = async () => {
    const response = await api.get('/api/settings');
    return response.data;
};

export const updateUserSettings = async (settings) => {
    const response = await api.post('/api/settings', settings);
    return response.data;
};

// ──────────────────────────────────────
// TRADE HISTORY
// ──────────────────────────────────────

export const getTradeHistory = async (limit = 50) => {
    const response = await api.get('/api/trade-history', {
        params: { limit }
    });
    return response.data;
};

// ──────────────────────────────────────
// ML TRAINING
// ──────────────────────────────────────

export const trainModels = async (coin, timeframe) => {
    const response = await api.post('/api/train-models', null, {
        params: { coin, timeframe }
    });
    return response.data;
};

export default api;
