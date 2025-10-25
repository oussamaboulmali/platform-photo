import Layout from '../../components/Layout';
import { useRouter } from 'next/router';
import { useQuery, useMutation } from '@tanstack/react-query';
import { imagesAPI, ordersAPI, walletAPI } from '../../lib/api';
import { toast } from 'react-toastify';
import { ShoppingCartIcon } from '@heroicons/react/24/outline';

export default function ImageDetail() {
  const router = useRouter();
  const { id } = router.query;

  const { data: image } = useQuery({
    queryKey: ['image', id],
    queryFn: () => imagesAPI.get(id),
    enabled: !!id
  });

  const { data: wallet } = useQuery({
    queryKey: ['wallet'],
    queryFn: walletAPI.get,
    retry: false
  });

  const purchaseMutation = useMutation({
    mutationFn: ({ licenseType, paymentMethod }) => 
      ordersAPI.create(id, licenseType, paymentMethod),
    onSuccess: (data) => {
      toast.success('Purchase successful!');
      router.push('/account/orders');
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Purchase failed');
    }
  });

  const handlePurchase = (licenseType, paymentMethod) => {
    if (!wallet) {
      router.push('/login');
      return;
    }
    purchaseMutation.mutate({ licenseType, paymentMethod });
  };

  if (!image) return <Layout><div className="text-center py-12">Loading...</div></Layout>;

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            {image.data.derivatives_list?.find(d => d.kind === 'preview') && (
              <img 
                src={`http://localhost:8020${image.data.derivatives_list.find(d => d.kind === 'preview').url}`}
                alt={image.data.filename}
                className="w-full rounded-lg shadow-lg"
              />
            )}
          </div>

          <div>
            <h1 className="text-3xl font-bold text-gray-900">{image.data.filename}</h1>
            <p className="mt-2 text-gray-600">{image.data.width} x {image.data.height} pixels</p>

            <div className="mt-6 space-y-4">
              <h2 className="text-xl font-semibold">License Options</h2>
              
              {[
                { type: 'standard', name: 'Standard License', price: '500 DZD', desc: 'For personal and commercial use' },
                { type: 'extended', name: 'Extended License', price: '1,500 DZD', desc: 'For extended commercial use' },
                { type: 'exclusive', name: 'Exclusive License', price: '5,000 DZD', desc: 'Exclusive rights' }
              ].map((license) => (
                <div key={license.type} className="border rounded-lg p-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="font-semibold">{license.name}</h3>
                      <p className="text-sm text-gray-600">{license.desc}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-bold text-indigo-600">{license.price}</p>
                      <button
                        onClick={() => handlePurchase(license.type, 'wallet')}
                        className="mt-2 bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 flex items-center"
                      >
                        <ShoppingCartIcon className="h-5 w-5 mr-1" />
                        Purchase
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {wallet && (
              <div className="mt-6 p-4 bg-gray-100 rounded-lg">
                <p className="text-sm text-gray-700">Your balance: {wallet.data.balance} {wallet.data.currency}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
