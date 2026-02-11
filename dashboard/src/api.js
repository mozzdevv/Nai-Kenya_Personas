import axios from 'axios';

const API_BASE = '/api';

// Create axios instance
const api = axios.create({
    baseURL: API_BASE,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle 401 responses
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Auth
export const login = async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const response = await api.post('/token', formData);
    return response.data;
};

export const getCurrentUser = () => api.get('/me');

// Posts
export const getPosts = (limit = 50) => api.get(`/posts?limit=${limit}`);

// Stats
export const getStats = () => api.get('/stats');

// RAG Activity
export const getRagActivity = (limit = 50) => api.get(`/rag?limit=${limit}`);

// LLM Routing
export const getRoutingStats = () => api.get('/routing');
export const getRoutingHistory = (limit = 50) => api.get(`/routing/history?limit=${limit}`);

// Validation
export const getValidationConfig = () => api.get('/validation/config');

// Errors
export const getErrors = (limit = 100, level = null) => {
    const params = new URLSearchParams({ limit });
    if (level) params.append('level', level);
    return api.get(`/errors?${params}`);
};

// WebSocket connection
export const createWebSocket = (token) => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    return new WebSocket(`${wsProtocol}//${wsHost}/api/ws?token=${token}`);
};

export default api;
