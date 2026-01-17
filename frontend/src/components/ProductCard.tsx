import { Product } from '../services/api';
import { useCartContext } from '../contexts/CartContext';

interface ProductCardProps {
  product: Product;
}

export default function ProductCard({ product }: ProductCardProps) {
  const { addToCart } = useCartContext();

  const handleAddToCart = () => {
    addToCart({
      product_id: product.id,
      quantity: 1,
      title: product.title,
      price: product.current_price_amount,
      formatted_price: product.formatted_price,
      image_url: product.image_url,
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      {product.image_url && (
        <img
          src={product.image_url}
          alt={product.title}
          className="w-full h-48 object-cover"
        />
      )}
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{product.title}</h3>
        {product.description && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">{product.description}</p>
        )}
        <div className="flex items-center justify-between gap-3">
          <span className="text-xl font-bold text-gray-900 min-w-0 truncate">
            {product.formatted_price || `$${(product.current_price_amount / 100).toFixed(2)}`}
          </span>
          <button
            type="button"
            onClick={handleAddToCart}
            className="flex-shrink-0 relative z-10 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors cursor-pointer"
          >
            Add to Cart
          </button>
        </div>
      </div>
    </div>
  );
}
