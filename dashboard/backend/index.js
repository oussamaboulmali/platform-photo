const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const axios = require('axios');
const jwt = require('jsonwebtoken');
const multer = require('multer');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8010;

// Middleware
app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN || 'http://localhost:3000', credentials: true }));
app.use(express.json());

// Rate limiting
const limiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 100 });
app.use('/api/', limiter);

// Service URLs
const AUTH_SERVICE = process.env.AUTH_SERVICE_URL || 'http://localhost:8001';
const IMAGE_SERVICE = process.env.IMAGE_SERVICE_URL || 'http://localhost:8002';
const ORDER_SERVICE = process.env.ORDER_SERVICE_URL || 'http://localhost:8003';
const ADMIN_SERVICE = process.env.ADMIN_SERVICE_URL || 'http://localhost:8004';

// JWT verification middleware
const verifyToken = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token provided' });

  try {
    const decoded = jwt.decode(token);
    req.user = decoded;
    req.headers['x-user-id'] = decoded.user_id;
    req.headers['x-user-email'] = decoded.email;
    req.headers['x-user-role'] = decoded.role;
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
app.get('/health', (req, res) => res.json({ status: 'ok', service: 'dashboard-gateway' }));

// Auth routes
app.post('/api/auth/login', (req, res) => proxyRequest(req, res, AUTH_SERVICE, '/api/auth/login/'));
app.post('/api/auth/register', (req, res) => proxyRequest(req, res, AUTH_SERVICE, '/api/auth/register/'));
app.post('/api/auth/logout', verifyToken, (req, res) => proxyRequest(req, res, AUTH_SERVICE, '/api/auth/logout/'));
app.post('/api/auth/2fa/setup', verifyToken, (req, res) => proxyRequest(req, res, AUTH_SERVICE, '/api/auth/setup_2fa/'));
app.post('/api/auth/2fa/verify', (req, res) => proxyRequest(req, res, AUTH_SERVICE, '/api/auth/verify_2fa/'));
app.get('/api/auth/me', verifyToken, (req, res) => proxyRequest(req, res, AUTH_SERVICE, '/api/auth/users/me/'));

// Image routes (upload, manage)
app.get('/api/images', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, '/api/images/'));
app.get('/api/images/:id', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, `/api/images/${req.params.id}/`));
app.post('/api/images/upload', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, '/api/images/upload/'));
app.post('/api/images/:id/submit', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, `/api/images/${req.params.id}/submit/`));
app.put('/api/images/:id/metadata', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, `/api/images/${req.params.id}/update_metadata/`));

// Review routes (validator)
app.get('/api/reviews/queue', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, '/api/reviews/queue/'));
app.post('/api/reviews/:id/approve', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, `/api/reviews/${req.params.id}/approve/`));
app.post('/api/reviews/:id/reject', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, `/api/reviews/${req.params.id}/reject/`));

// Admin routes (categories, topics, places)
app.get('/api/categories', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, '/api/categories/'));
app.post('/api/categories', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, '/api/categories/'));
app.get('/api/topics', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, '/api/topics/'));
app.post('/api/topics', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, '/api/topics/'));
app.get('/api/places', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, '/api/places/'));
app.post('/api/places', verifyToken, (req, res) => proxyRequest(req, res, IMAGE_SERVICE, '/api/places/'));

// Bloc and Ad management
app.get('/api/blocs', verifyToken, (req, res) => proxyRequest(req, res, ADMIN_SERVICE, '/api/blocs/'));
app.post('/api/blocs', verifyToken, (req, res) => proxyRequest(req, res, ADMIN_SERVICE, '/api/blocs/'));
app.put('/api/blocs/:id', verifyToken, (req, res) => proxyRequest(req, res, ADMIN_SERVICE, `/api/blocs/${req.params.id}/`));
app.delete('/api/blocs/:id', verifyToken, (req, res) => proxyRequest(req, res, ADMIN_SERVICE, `/api/blocs/${req.params.id}/`));
app.get('/api/ads', verifyToken, (req, res) => proxyRequest(req, res, ADMIN_SERVICE, '/api/ads/'));
app.post('/api/ads', verifyToken, (req, res) => proxyRequest(req, res, ADMIN_SERVICE, '/api/ads/'));

// Subscription management
app.get('/api/subscriptions/plans', verifyToken, (req, res) => proxyRequest(req, res, ORDER_SERVICE, '/api/plans/'));
app.post('/api/subscriptions/plans', verifyToken, (req, res) => proxyRequest(req, res, ORDER_SERVICE, '/api/plans/'));
app.get('/api/subscriptions', verifyToken, (req, res) => proxyRequest(req, res, ORDER_SERVICE, '/api/subscriptions/'));
app.post('/api/subscriptions/:id/approve', verifyToken, (req, res) => proxyRequest(req, res, ORDER_SERVICE, `/api/subscriptions/${req.params.id}/approve/`));

// Top-up management
app.get('/api/topups', verifyToken, (req, res) => proxyRequest(req, res, ORDER_SERVICE, '/api/topups/'));
app.post('/api/topups/:id/approve', verifyToken, (req, res) => proxyRequest(req, res, ORDER_SERVICE, `/api/topups/${req.params.id}/approve/`));

// User management
app.get('/api/users', verifyToken, (req, res) => proxyRequest(req, res, AUTH_SERVICE, '/api/auth/users/'));
app.get('/api/users/:id', verifyToken, (req, res) => proxyRequest(req, res, AUTH_SERVICE, `/api/auth/users/${req.params.id}/`));

app.listen(PORT, () => console.log(`Dashboard gateway running on port ${PORT}`));
