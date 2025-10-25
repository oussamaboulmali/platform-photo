import { useQuery } from '@tanstack/react-query';
import { imagesAPI } from '../lib/api';

export default function MyImages() {
  const { data: images, isLoading } = useQuery({
    queryKey: ['my-images'],
    queryFn: () => imagesAPI.list()
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900">My Images</h1>
      
      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {images?.data?.results?.map((image) => (
          <div key={image.id} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="aspect-w-16 aspect-h-9 bg-gray-200">
              {image.thumbnail_url && (
                <img src={`http://localhost:8010${image.thumbnail_url}`} alt={image.filename} className="object-cover" />
              )}
            </div>
            <div className="p-4">
              <h3 className="text-sm font-medium text-gray-900 truncate">{image.filename}</h3>
              <p className="mt-1 text-sm text-gray-500">{image.width} x {image.height}</p>
              <div className="mt-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                  ${image.status === 'published' ? 'bg-green-100 text-green-800' :
                    image.status === 'submitted' ? 'bg-yellow-100 text-yellow-800' :
                    image.status === 'rejected' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'}`}>
                  {image.status}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
