import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewsAPI } from '../lib/api';
import { toast } from 'react-toastify';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

export default function ReviewQueue() {
  const queryClient = useQueryClient();
  const { data: queue, isLoading } = useQuery({
    queryKey: ['review-queue'],
    queryFn: reviewsAPI.getQueue
  });

  const approveMutation = useMutation({
    mutationFn: (id) => reviewsAPI.approve(id, { comment: 'Approved' }),
    onSuccess: () => {
      queryClient.invalidateQueries(['review-queue']);
      toast.success('Image approved!');
    }
  });

  const rejectMutation = useMutation({
    mutationFn: (id) => reviewsAPI.reject(id, { comment: 'Quality issues' }),
    onSuccess: () => {
      queryClient.invalidateQueries(['review-queue']);
      toast.success('Image rejected');
    }
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900">Review Queue</h1>
      <p className="mt-2 text-sm text-gray-700">{queue?.data?.length || 0} images pending review</p>

      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {queue?.data?.map((image) => (
          <div key={image.id} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="aspect-w-16 aspect-h-9 bg-gray-200">
              {image.preview_url && (
                <img src={`http://localhost:8010${image.preview_url}`} alt={image.filename} className="object-cover" />
              )}
            </div>
            <div className="p-4">
              <h3 className="text-sm font-medium text-gray-900 truncate">{image.filename}</h3>
              <p className="mt-1 text-sm text-gray-500">{image.width} x {image.height}</p>
              <div className="mt-4 flex gap-2">
                <button
                  onClick={() => approveMutation.mutate(image.id)}
                  className="flex-1 inline-flex justify-center items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                >
                  <CheckCircleIcon className="h-5 w-5 mr-1" />
                  Approve
                </button>
                <button
                  onClick={() => rejectMutation.mutate(image.id)}
                  className="flex-1 inline-flex justify-center items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
                >
                  <XCircleIcon className="h-5 w-5 mr-1" />
                  Reject
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
