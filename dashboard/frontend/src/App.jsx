import { Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './stores/authStore';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import MyImages from './pages/MyImages';
import ReviewQueue from './pages/ReviewQueue';
import Categories from './pages/Categories';
import Topics from './pages/Topics';
import Places from './pages/Places';
import Blocs from './pages/Blocs';
import Ads from './pages/Ads';
import Subscriptions from './pages/Subscriptions';
import TopUps from './pages/TopUps';
import Users from './pages/Users';

const PrivateRoute = ({ children, roles }) => {
  const { user } = useAuthStore();
  
  if (!user) {
    return <Navigate to="/login" />;
  }
  
  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" />;
  }
  
  return children;
};

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
        <Route index element={<Navigate to="/dashboard" />} />
        <Route path="dashboard" element={<Dashboard />} />
        
        {/* Upload and Manage Images */}
        <Route path="upload" element={<PrivateRoute roles={['photographer', 'infographiste', 'admin']}><Upload /></PrivateRoute>} />
        <Route path="my-images" element={<PrivateRoute roles={['photographer', 'infographiste', 'admin']}><MyImages /></PrivateRoute>} />
        
        {/* Validator */}
        <Route path="review" element={<PrivateRoute roles={['validator', 'admin']}><ReviewQueue /></PrivateRoute>} />
        
        {/* Admin - Content Management */}
        <Route path="categories" element={<PrivateRoute roles={['admin']}><Categories /></PrivateRoute>} />
        <Route path="topics" element={<PrivateRoute roles={['admin']}><Topics /></PrivateRoute>} />
        <Route path="places" element={<PrivateRoute roles={['admin']}><Places /></PrivateRoute>} />
        <Route path="blocs" element={<PrivateRoute roles={['admin']}><Blocs /></PrivateRoute>} />
        <Route path="ads" element={<PrivateRoute roles={['admin']}><Ads /></PrivateRoute>} />
        
        {/* Admin - Financial */}
        <Route path="subscriptions" element={<PrivateRoute roles={['admin']}><Subscriptions /></PrivateRoute>} />
        <Route path="topups" element={<PrivateRoute roles={['admin']}><TopUps /></PrivateRoute>} />
        
        {/* Admin - Users */}
        <Route path="users" element={<PrivateRoute roles={['admin']}><Users /></PrivateRoute>} />
      </Route>
    </Routes>
  );
}

export default App;
