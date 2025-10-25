import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8010';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authAPI = {
  login: (email, password) => api.post('/api/auth/login', { email, password }),
  register: (data) => api.post('/api/auth/register', data),
  logout: () => api.post('/api/auth/logout'),
  getMe: () => api.get('/api/auth/me'),
  setup2FA: (enable) => api.post('/api/auth/2fa/setup', { enable }),
  verify2FA: (token) => api.post('/api/auth/2fa/verify', { token }),
};

// Images API
export const imagesAPI = {
  list: (params) => api.get('/api/images', { params }),
  get: (id) => api.get(`/api/images/${id}`),
  upload: (formData) => api.post('/api/images/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  updateMetadata: (id, data) => api.put(`/api/images/${id}/metadata`, data),
  submit: (id) => api.post(`/api/images/${id}/submit`),
};

// Reviews API
export const reviewsAPI = {
  getQueue: () => api.get('/api/reviews/queue'),
  approve: (id, data) => api.post(`/api/reviews/${id}/approve`, data),
  reject: (id, data) => api.post(`/api/reviews/${id}/reject`, data),
};

// Categories API
export const categoriesAPI = {
  list: () => api.get('/api/categories'),
  create: (data) => api.post('/api/categories', data),
  update: (id, data) => api.put(`/api/categories/${id}`, data),
  delete: (id) => api.delete(`/api/categories/${id}`),
};

// Topics API
export const topicsAPI = {
  list: () => api.get('/api/topics'),
  create: (data) => api.post('/api/topics', data),
};

// Places API
export const placesAPI = {
  list: () => api.get('/api/places'),
  create: (data) => api.post('/api/places', data),
};

// Blocs API
export const blocsAPI = {
  list: () => api.get('/api/blocs'),
  create: (data) => api.post('/api/blocs', data),
  update: (id, data) => api.put(`/api/blocs/${id}`, data),
  delete: (id) => api.delete(`/api/blocs/${id}`),
};

// Ads API
export const adsAPI = {
  list: () => api.get('/api/ads'),
  create: (data) => api.post('/api/ads', data),
  update: (id, data) => api.put(`/api/ads/${id}`, data),
  delete: (id) => api.delete(`/api/ads/${id}`),
};

// Subscriptions API
export const subscriptionsAPI = {
  listPlans: () => api.get('/api/subscriptions/plans'),
  createPlan: (data) => api.post('/api/subscriptions/plans', data),
  listSubscriptions: () => api.get('/api/subscriptions'),
  approveSubscription: (id, data) => api.post(`/api/subscriptions/${id}/approve`, data),
};

// Top-ups API
export const topupsAPI = {
  list: () => api.get('/api/topups'),
  approve: (id, data) => api.post(`/api/topups/${id}/approve`, data),
};

// Users API
export const usersAPI = {
  list: () => api.get('/api/users'),
  get: (id) => api.get(`/api/users/${id}`),
};
