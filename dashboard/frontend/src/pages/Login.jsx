import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { authAPI } from '../lib/api';
import useAuthStore from '../stores/authStore';
import { toast } from 'react-toastify';

export default function Login() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [loading, setLoading] = useState(false);
  const [requires2FA, setRequires2FA] = useState(false);

  const onSubmit = async (data) => {
    setLoading(true);
    try {
      if (requires2FA) {
        const response = await authAPI.verify2FA(data.token);
        setAuth(response.data.user, response.data.tokens.access);
        toast.success('Login successful!');
        navigate('/dashboard');
      } else {
        const response = await authAPI.login(data.email, data.password);
        if (response.data.requires_2fa) {
          setRequires2FA(true);
          toast.info('Please enter your 2FA code');
        } else {
          setAuth(response.data.user, response.data.tokens.access);
          toast.success('Login successful!');
          navigate('/dashboard');
        }
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Agency Dashboard
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {requires2FA ? 'Enter your 2FA code' : 'Sign in to your account'}
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          {!requires2FA ? (
            <>
              <div>
                <label htmlFor="email" className="sr-only">Email address</label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  {...register('email', { required: 'Email is required' })}
                  className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                  placeholder="Email address"
                />
                {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>}
              </div>
              <div>
                <label htmlFor="password" className="sr-only">Password</label>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  {...register('password', { required: 'Password is required' })}
                  className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                  placeholder="Password"
                />
                {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>}
              </div>
            </>
          ) : (
            <div>
              <label htmlFor="token" className="sr-only">2FA Token</label>
              <input
                id="token"
                type="text"
                {...register('token', { required: '2FA token is required', minLength: 6, maxLength: 6 })}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Enter 6-digit code"
                maxLength={6}
              />
              {errors.token && <p className="text-red-500 text-sm mt-1">{errors.token.message}</p>}
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Loading...' : (requires2FA ? 'Verify' : 'Sign in')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
