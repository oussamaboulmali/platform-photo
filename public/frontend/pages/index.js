import Layout from '../components/Layout';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { imagesAPI, blocsAPI } from '../lib/api';

export default function Home() {
  const { data: blocs } = useQuery({ queryKey: ['blocs'], queryFn: blocsAPI.list });
  const { data: images } = useQuery({ 
    queryKey: ['featured-images'], 
    queryFn: () => imagesAPI.search({ status: 'published', limit: 12 })
  });

  return (
    <Layout>
      <div className="bg-indigo-700 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl font-extrabold text-white sm:text-5xl md:text-6xl">
            Find the Perfect Image
          </h1>
          <p className="mt-3 max-w-md mx-auto text-base text-indigo-200 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
            Browse thousands of high-quality images from professional photographers
          </p>
          <div className="mt-10">
            <Link href="/search" className="inline-block bg-white text-indigo-600 px-8 py-3 rounded-md font-semibold hover:bg-gray-100">
              Start Browsing
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Featured Images</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {images?.data?.results?.slice(0, 8).map((image) => (
            <Link key={image.id} href={`/images/${image.id}`}>
              <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition">
                <div className="aspect-w-16 aspect-h-9 bg-gray-200">
                  {image.preview_url && (
                    <img src={`http://localhost:8020${image.preview_url}`} alt={image.filename} className="object-cover w-full h-48" />
                  )}
                </div>
                <div className="p-4">
                  <h3 className="text-sm font-medium text-gray-900 truncate">{image.filename}</h3>
                  <p className="text-xs text-gray-500 mt-1">{image.width} x {image.height}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      <div className="bg-gray-100 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Subscription Plans</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
            {[
              { name: '1 Month', price: '2,500 DZD', downloads: '10' },
              { name: '3 Months', price: '6,500 DZD', downloads: '35' },
              { name: '6 Months', price: '12,000 DZD', downloads: '80' },
            ].map((plan) => (
              <div key={plan.name} className="bg-white rounded-lg shadow p-6 text-center">
                <h3 className="text-lg font-semibold">{plan.name}</h3>
                <p className="text-3xl font-bold text-indigo-600 mt-4">{plan.price}</p>
                <p className="text-gray-600 mt-2">{plan.downloads} downloads</p>
                <Link href="/account/subscriptions" className="mt-6 block w-full bg-indigo-600 text-white py-2 rounded-md hover:bg-indigo-700">
                  Subscribe
                </Link>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}
