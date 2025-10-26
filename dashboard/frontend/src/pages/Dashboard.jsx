import { useQuery } from '@tanstack/react-query';
import useAuthStore from '../stores/authStore';
import { imagesAPI } from '../lib/api';
import { PhotoIcon, CheckCircleIcon, ClockIcon, XCircleIcon } from '@heroicons/react/24/outline';

export default function Dashboard() {
  const { user } = useAuthStore();
  const { data: images } = useQuery({
    queryKey: ['images', 'dashboard'],
    queryFn: () => imagesAPI.list({ limit: 10 }),
  });

  const stats = [
    { name: 'Total Images', value: images?.data?.count || 0, icon: PhotoIcon, color: 'text-blue-600' },
    { name: 'Published', value: images?.data?.results?.filter(img => img.status === 'published').length || 0, icon: CheckCircleIcon, color: 'text-green-600' },
    { name: 'Pending', value: images?.data?.results?.filter(img => img.status === 'submitted').length || 0, icon: ClockIcon, color: 'text-yellow-600' },
    { name: 'Rejected', value: images?.data?.results?.filter(img => img.status === 'rejected').length || 0, icon: XCircleIcon, color: 'text-red-600' },
  ];

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
      <p className="mt-2 text-sm text-gray-700">Welcome back, {user?.first_name || user?.email}</p>

      <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <stat.icon className={`h-6 w-6 ${stat.color}`} aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">{stat.name}</dt>
                    <dd className="text-2xl font-semibold text-gray-900">{stat.value}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8">
        <h2 className="text-lg font-medium text-gray-900">Recent Activity</h2>
        <div className="mt-4 bg-white shadow overflow-hidden sm:rounded-md">
          <ul role="list" className="divide-y divide-gray-200">
            {images?.data?.results?.slice(0, 5).map((image) => (
              <li key={image.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-indigo-600 truncate">{image.filename}</p>
                    <div className="ml-2 flex-shrink-0 flex">
                      <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${image.status === 'published' ? 'bg-green-100 text-green-800' : 
                          image.status === 'submitted' ? 'bg-yellow-100 text-yellow-800' : 
                          'bg-gray-100 text-gray-800'}`}>
                        {image.status}
                      </p>
                    </div>
                  </div>
                  <div className="mt-2 sm:flex sm:justify-between">
                    <div className="sm:flex">
                      <p className="flex items-center text-sm text-gray-500">
                        {image.width} x {image.height} • {(image.filesize / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                      <p>{new Date(image.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
