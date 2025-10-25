const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const axios = require('axios');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8020;

// Middleware
app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN || 'http://localhost:3001', credentials: true }));
app.use(express.json());

// Rate limiting
const limiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 200 });
app.use('/api/', limiter);

// Service URLs
const AUTH_SERVICE = process.env.AUTH_SERVICE_URL || 'http://localhost:8001';
const IMAGE_SERVICE = process.env.IMAGE_SERVICE_URL || 'http://localhost:8002';
const ORDER_SERVICE = process.env.ORDER_SERVICE_URL || 'http://localhost:8003';
const ADMIN_SERVICE = process.env.ADMIN_SERVICE_URL || 'http://localhost:8004';

// Optional token verification (for logged-in users)
const optionalAuth = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (token) {
    try {
      const decoded = jwt.decode(token);
      req.user = decoded;
      req.headers['x-user-id'] = decoded.user_id;
      req.headers['x-user-email'] = decoded.email;
      req.headers['x-user-role'] = 'customer';
    } catch (err) {}
  }
  next();
};

// Required auth
const requireAuth = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Authentication required' });

  try {
    const decoded = jwt.decode(token);
    req.user = decoded;
    req.headers['x-user-id'] = decoded.user_id;
    req.headers['x-user-email'] = decoded.email;
    req.headers['x-user-role'] = 'customer';
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid token' });
  }
};

// Proxy helper
const proxyRequest = async (req, res, serviceUrl, path) => {
  try {
    const response = await axios({
      method: req.method,
      url: `${serviceUrl}${path}`,
      data: req.body,
      params: req.query,
      headers: {
        'Authorization': req.headers.authorization,
        'X-User-Id': req.headers['x-user-id'],
        'X-User-Email': req.headers['x-user-email'],
        'X-User-Role': req.headers['x-user-role'],
      }
    });
    res.status(response.status).json(response.data);
  } catch (error) {
    const status = error.response?.status || 500;
    const data = error.response?.data || { error: 'Service unavailable' };
    res.status(status).json(data);
  }
};

// Health check
app.get('/health', (req, res) => res.json({ status: 'ok', service: 'public-gateway' }));

// Public auth routes
app.post('/api/auth/register', (req, res) => proxyRequest(req, res, AUTH_SERVICE, '/api/auth/register/'));
app.post('/api/auth/login', (req, res) => proxyRequest(req, res, AUTH_SERVICE, '/api/auth/login/'));
app.post('/api/auth/logout', requireAuth, (req, res) => proxyRequest(req, res, AUTH_SERVICE, '/api/auth/logout/'));
app.get('/api/auth/me', requireAuth, (req, res) => proxyRequest(req, res, AUTH_SERVICE, '/api/auth/users/me/'));

// Public image search and browse
app.get('/api/images/search', optionalAuth, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, '/api/images/search/'));
app.get('/api/images/:id', optionalAuth, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, `/api/images/${req.params.id}/`));

// Categories, topics, places (public)
app.get('/api/categories', (req, res) => proxyRequest(req, res, IMAGE_SERVICE, '/api/categories/'));
app.get('/api/topics', (req, res) => proxyRequest(req, res, IMAGE_SERVICE, '/api/topics/'));
app.get('/api/places', (req, res) => proxyRequest(req, res, IMAGE_SERVICE, '/api/places/'));

// Blocs and ads (public)
app.get('/api/blocs', (req, res) => proxyRequest(req, res, ADMIN_SERVICE, '/api/blocs/'));
app.get('/api/ads', (req, res) => proxyRequest(req, res, ADMIN_SERVICE, '/api/ads/'));

// Subscription plans (public)
app.get('/api/plans', (req, res) => proxyRequest(req, res, ORDER_SERVICE, '/api/plans/'));

// Wallet (user)
app.get('/api/wallet', requireAuth, (req, res) => proxyRequest(req, res, ORDER_SERVICE, '/api/wallets/my_wallet/'));
app.get('/api/wallet/transactions', requireAuth, (req, res) => proxyRequest(req, res, ORDER_SERVICE, '/api/wallets/my_transactions/'));

// Top-up requests (user)
app.post('/api/topup', requireAuth, (req, res) => proxyRequest(req, res, ORDER_SERVICE, '/api/topups/'));
app.get('/api/topup/history', requireAuth, (req, res) => proxyRequest(req, res, ORDER_SERVICE, '/api/topups/'));

// Subscriptions (user)
app.post('/api/subscribe', requireAuth, (req, res) => proxyRequest(req, res, ORDER_SERVICE, '/api/subscriptions/subscribe/'));
app.get('/api/subscriptions', requireAuth, (req, res) => proxyRequest(req, res, ORDER_SERVICE, '/api/subscriptions/my_subscriptions/'));

// Orders (user)
app.post('/api/order', requireAuth, (req, res) => proxyRequest(req, res, ORDER_SERVICE, '/api/orders/create_order/'));
app.get('/api/orders', requireAuth, (req, res) => proxyRequest(req, res, ORDER_SERVICE, '/api/orders/'));
app.get('/api/orders/:id', requireAuth, (req, res) => proxyRequest(req, res, ORDER_SERVICE, `/api/orders/${req.params.id}/`));

// Download
app.get('/api/download/:token', requireAuth, (req, res) => proxyRequest(req, res, ORDER_SERVICE, `/api/orders/download/${req.params.token}/`));

// Media proxy (for serving images)
app.use('/media', express.static(process.env.STORAGE_ROOT || '/var/www/agency_storage'));

app.listen(PORT, () => console.log(`Public gateway running on port ${PORT}`));
