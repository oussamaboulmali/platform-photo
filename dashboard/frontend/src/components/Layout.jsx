import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import useAuthStore from '../stores/authStore';
import { authAPI } from '../lib/api';
import { toast } from 'react-toastify';
import {
  HomeIcon, PhotoIcon, CheckCircleIcon, TagIcon, MapPinIcon,
  CubeIcon, MegaphoneIcon, CreditCardIcon, UsersIcon,
  ArrowRightOnRectangleIcon, Bars3Icon, XMarkIcon
} from '@heroicons/react/24/outline';

export default function Layout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      logout();
      navigate('/login');
      toast.success('Logged out successfully');
    }
  };

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon, roles: ['photographer', 'infographiste', 'validator', 'admin'] },
    { name: 'Upload', href: '/upload', icon: PhotoIcon, roles: ['photographer', 'infographiste', 'admin'] },
    { name: 'My Images', href: '/my-images', icon: PhotoIcon, roles: ['photographer', 'infographiste', 'admin'] },
    { name: 'Review Queue', href: '/review', icon: CheckCircleIcon, roles: ['validator', 'admin'] },
    { name: 'Categories', href: '/categories', icon: TagIcon, roles: ['admin'] },
    { name: 'Topics', href: '/topics', icon: TagIcon, roles: ['admin'] },
    { name: 'Places', href: '/places', icon: MapPinIcon, roles: ['admin'] },
    { name: 'Blocs', href: '/blocs', icon: CubeIcon, roles: ['admin'] },
    { name: 'Ads', href: '/ads', icon: MegaphoneIcon, roles: ['admin'] },
    { name: 'Subscriptions', href: '/subscriptions', icon: CreditCardIcon, roles: ['admin'] },
    { name: 'Top-ups', href: '/topups', icon: CreditCardIcon, roles: ['admin'] },
    { name: 'Users', href: '/users', icon: UsersIcon, roles: ['admin'] },
  ].filter(item => item.roles.includes(user?.role));

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-40 lg:hidden ${sidebarOpen ? '' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)}></div>
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white">
          <div className="flex items-center justify-between px-4 py-4 border-b">
            <h1 className="text-xl font-bold text-gray-900">Agency Dashboard</h1>
            <button onClick={() => setSidebarOpen(false)}><XMarkIcon className="h-6 w-6" /></button>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className="group flex items-center px-2 py-2 text-sm font-medium rounded-md hover:bg-gray-100"
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="mr-3 h-6 w-6" />
                {item.name}
              </Link>
            ))}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-white border-r border-gray-200">
          <div className="flex items-center flex-shrink-0 px-4 py-4 border-b">
            <h1 className="text-xl font-bold text-gray-900">Agency Dashboard</h1>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className="group flex items-center px-2 py-2 text-sm font-medium rounded-md hover:bg-gray-100"
              >
                <item.icon className="mr-3 h-6 w-6" />
                {item.name}
              </Link>
            ))}
          </nav>
          <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-700">{user?.email}</p>
              <p className="text-xs text-gray-500">{user?.role}</p>
            </div>
            <button
              onClick={handleLogout}
              className="ml-3 text-gray-400 hover:text-gray-500"
            >
              <ArrowRightOnRectangleIcon className="h-6 w-6" />
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        <div className="sticky top-0 z-10 flex h-16 flex-shrink-0 bg-white shadow lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="px-4 text-gray-500 focus:outline-none lg:hidden"
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
          <div className="flex flex-1 justify-between px-4">
            <div className="flex flex-1"></div>
          </div>
        </div>

        <main className="flex-1">
          <div className="py-6">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <Outlet />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
