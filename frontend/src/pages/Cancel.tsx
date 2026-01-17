import { Link } from 'react-router-dom';

export default function Cancel() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Checkout Cancelled</h1>
        <p className="text-lg text-gray-600 mb-8">
          Your checkout was cancelled. No charges were made.
        </p>
        <div className="space-x-4">
          <Link
            to="/cart"
            className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            Return to Cart
          </Link>
          <Link
            to="/"
            className="inline-block px-6 py-3 bg-gray-200 text-gray-900 rounded-md hover:bg-gray-300"
          >
            Continue Shopping
          </Link>
        </div>
      </div>
    </div>
  );
}
