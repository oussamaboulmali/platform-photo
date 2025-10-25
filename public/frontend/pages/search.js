import Layout from '../components/Layout';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useQuery } from '@tanstack/react-query';
import { imagesAPI } from '../lib/api';

export default function Search() {
  const router = useRouter();
  const { q, category, orientation } = router.query;

  const { data: images, isLoading } = useQuery({
    queryKey: ['search', q, category, orientation],
    queryFn: () => imagesAPI.search({ q, category, orientation, status: 'published' }),
    enabled: !!q || !!category || !!orientation
  });

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-bold text-gray-900">
          {q ? `Search Results for "${q}"` : 'Browse Images'}
        </h1>

        {isLoading ? (
          <div className="text-center py-12">Loading...</div>
        ) : (
          <>
            <p className="mt-2 text-sm text-gray-600">
              {images?.data?.results?.length || 0} images found
            </p>

            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {images?.data?.results?.map((image) => (
                <Link key={image.id} href={`/images/${image.id}`}>
                  <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition cursor-pointer">
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
          </>
        )}
      </div>
    </Layout>
  );
}
