import { Link } from 'react-router-dom';
import { Product } from '../services/api';
import { deleteProduct, resyncProduct } from '../services/api';
import { useState } from 'react';

interface AdminProductListProps {
  products: Product[];
  onUpdate: () => void;
}

export default function AdminProductList({ products, onUpdate }: AdminProductListProps) {
  const [loading, setLoading] = useState<number | null>(null);

  const handleRemove = async (id: number) => {
    if (!confirm('Are you sure you want to remove this product?')) return;
    try {
      await deleteProduct(id);
      onUpdate();
    } catch (error) {
      alert('Failed to remove product');
      console.error(error);
    }
  };

  const handleResync = async (id: number) => {
    setLoading(id);
    try {
      await resyncProduct(id);
      onUpdate();
    } catch (error) {
      alert('Failed to resync product');
      console.error(error);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Product
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Price
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider max-w-[200px]">
              Stripe Sync
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap min-w-[220px] sticky right-0 bg-gray-50 z-10 border-l border-gray-200">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {products.map((product) => (
            <tr key={product.id}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  {product.image_url && (
                    <img
                      src={product.image_url}
                      alt={product.title}
                      className="h-10 w-10 rounded object-cover mr-3"
                    />
                  )}
                  <div>
                    <div className="text-sm font-medium text-gray-900">{product.title}</div>
                    <div className="text-sm text-gray-500">
                      {product.published ? (
                        <span className="text-green-600">Published</span>
                      ) : (
                        <span className="text-gray-400">Draft</span>
                      )}
                    </div>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {product.formatted_price || `$${(product.current_price_amount / 100).toFixed(2)}`}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span
                  className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    product.published
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {product.published ? 'Published' : 'Draft'}
                </span>
              </td>
              <td className="px-6 py-4 text-sm text-gray-500 max-w-[220px]">
                <div className="truncate" title={[product.last_sync_status, product.active_stripe_price_id].filter(Boolean).join(' | ') || 'Not synced'}>
                  <div>Status: {product.last_sync_status || 'Not synced'}</div>
                  {product.active_stripe_price_id && (
                    <div className="text-xs truncate">Price ID: {product.active_stripe_price_id}...</div>
                  )}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium min-w-[220px] sticky right-0 bg-white z-10 border-l border-gray-100">
                <div className="flex justify-end gap-2">
                  <Link
                    to={`/admin/products/${product.id}/edit`}
                    className="text-indigo-600 hover:text-indigo-900"
                  >
                    Edit
                  </Link>
                  <button
                    onClick={() => handleResync(product.id)}
                    disabled={loading === product.id}
                    className="text-blue-600 hover:text-blue-900 disabled:opacity-50"
                  >
                    {loading === product.id ? 'Syncing...' : 'Resync'}
                  </button>
                  <button
                    onClick={() => handleRemove(product.id)}
                    className="text-red-600 hover:text-red-900"
                  >
                    Remove
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
