import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { getOrderBySession, Order } from '../services/api';
import { useCartContext } from '../contexts/CartContext';

export default function Success() {
  const [searchParams] = useSearchParams();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const { clearCart } = useCartContext();
  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    if (sessionId) {
      getOrderBySession(sessionId)
        .then((data) => {
          setOrder(data);
          clearCart(); // Clear cart on successful order
        })
        .catch((error) => {
          console.error('Error fetching order:', error);
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, [sessionId, clearCart]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">Loading order details...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-8 text-center">
        <div className="mb-6">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
            <svg
              className="h-6 w-6 text-green-600"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Thank you for your order!</h1>
        <p className="text-lg text-gray-600 mb-8">
          Your payment was successful. We've received your order and will process it shortly.
        </p>
        {order && (
          <div className="bg-gray-50 rounded-lg p-6 mb-6 text-left">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Order Details</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Order ID:</span>
                <span className="font-medium text-gray-900">#{order.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className="font-medium text-gray-900 capitalize">{order.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total:</span>
                <span className="font-medium text-gray-900">
                  ${(order.total_amount_snapshot / 100).toFixed(2)}
                </span>
              </div>
              {order.customer_email && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Email:</span>
                  <span className="font-medium text-gray-900">{order.customer_email}</span>
                </div>
              )}
            </div>
          </div>
        )}
        <Link
          to="/"
          className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          Continue Shopping
        </Link>
      </div>
    </div>
  );
}
