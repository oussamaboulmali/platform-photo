import Layout from '../components/Layout';
import { useQuery } from '@tanstack/react-query';
import { walletAPI, ordersAPI, subscriptionsAPI } from '../lib/api';
import Link from 'next/link';

export default function Account() {
  const { data: wallet } = useQuery({ queryKey: ['wallet'], queryFn: walletAPI.get });
  const { data: orders } = useQuery({ queryKey: ['orders'], queryFn: ordersAPI.list });
  const { data: subscriptions } = useQuery({ queryKey: ['subscriptions'], queryFn: subscriptionsAPI.mySubscriptions });

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-bold text-gray-900">My Account</h1>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900">Wallet Balance</h2>
            <p className="mt-2 text-3xl font-bold text-indigo-600">
              {wallet?.data?.balance || 0} {wallet?.data?.currency || 'DZD'}
            </p>
            <Link href="/account/topup" className="mt-4 inline-block text-indigo-600 hover:text-indigo-700">
              Top up →
            </Link>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900">Orders</h2>
            <p className="mt-2 text-3xl font-bold text-gray-900">{orders?.data?.length || 0}</p>
            <Link href="/account/orders" className="mt-4 inline-block text-indigo-600 hover:text-indigo-700">
              View orders →
            </Link>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900">Active Subscriptions</h2>
            <p className="mt-2 text-3xl font-bold text-gray-900">
              {subscriptions?.data?.filter(s => s.status === 'active').length || 0}
            </p>
            <Link href="/account/subscriptions" className="mt-4 inline-block text-indigo-600 hover:text-indigo-700">
              Manage →
            </Link>
          </div>
        </div>

        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900">Recent Orders</h2>
          <div className="mt-4 bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {orders?.data?.slice(0, 5).map((order) => (
                <li key={order.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{order.image_filename}</p>
                      <p className="text-sm text-gray-500">{order.license_type} license</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">{order.amount} {order.currency}</p>
                      <p className={`text-sm ${order.payment_status === 'paid' ? 'text-green-600' : 'text-yellow-600'}`}>
                        {order.payment_status}
                      </p>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </Layout>
  );
}
