import Link from 'next/link';
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import { MagnifyingGlassIcon, ShoppingCartIcon, UserCircleIcon } from '@heroicons/react/24/outline';

export default function Layout({ children }) {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const userData = typeof window !== 'undefined' ? localStorage.getItem('user') : null;
    if (userData) setUser(JSON.parse(userData));
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="text-2xl font-bold text-indigo-600">
                Agency
              </Link>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link href="/search" className="text-gray-700 hover:text-indigo-600 px-3 py-2">
                  Browse
                </Link>
                <Link href="/categories" className="text-gray-700 hover:text-indigo-600 px-3 py-2">
                  Categories
                </Link>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <form onSubmit={handleSearch} className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search images..."
                  className="w-64 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button type="submit" className="absolute right-2 top-2.5">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </button>
              </form>

              {user ? (
                <Link href="/account" className="flex items-center text-gray-700 hover:text-indigo-600">
                  <UserCircleIcon className="h-6 w-6 mr-1" />
                  Account
                </Link>
              ) : (
                <Link href="/login" className="text-gray-700 hover:text-indigo-600">
                  Sign In
                </Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main>{children}</main>

      <footer className="bg-white mt-12 border-t">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-gray-500 text-sm">
            © 2025 Agency Platform. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
