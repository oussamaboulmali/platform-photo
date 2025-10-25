import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8020';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

export const authAPI = {
  login: (email, password) => api.post('/api/auth/login', { email, password }),
  register: (data) => api.post('/api/auth/register', data),
  logout: () => api.post('/api/auth/logout'),
  getMe: () => api.get('/api/auth/me'),
};

export const imagesAPI = {
  search: (params) => api.get('/api/images/search', { params }),
  get: (id) => api.get(`/api/images/${id}`),
};

export const categoriesAPI = {
  list: () => api.get('/api/categories'),
};

export const blocsAPI = {
  list: () => api.get('/api/blocs'),
};

export const walletAPI = {
  get: () => api.get('/api/wallet'),
  getTransactions: () => api.get('/api/wallet/transactions'),
  topup: (amount) => api.post('/api/topup', { amount }),
};

export const subscriptionsAPI = {
  listPlans: () => api.get('/api/plans'),
  subscribe: (planId) => api.post('/api/subscribe', { plan_id: planId }),
  mySubscriptions: () => api.get('/api/subscriptions'),
};

export const ordersAPI = {
  create: (imageId, licenseType, paymentMethod) => 
    api.post('/api/order', { image_id: imageId, license_type: licenseType, payment_method: paymentMethod }),
  list: () => api.get('/api/orders'),
  download: (token) => api.get(`/api/download/${token}`),
};
