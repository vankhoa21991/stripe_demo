import { useState } from 'react';
import { Product } from '../services/api';
import { useCartContext } from '../contexts/CartContext';

interface ProductCardProps {
  product: Product;
}

export default function ProductCard({ product }: ProductCardProps) {
  const { addToCart } = useCartContext();
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  // Get images array (support both images and image_url for backward compatibility)
  const images = product.images && product.images.length > 0 
    ? product.images 
    : (product.image_url ? [product.image_url] : []);
  
  const currentImage = images[currentImageIndex] || null;

  const handleAddToCart = () => {
    addToCart({
      product_id: product.id,
      quantity: 1,
      title: product.title,
      price: product.current_price_amount,
      formatted_price: product.formatted_price,
      image_url: currentImage,
    });
  };

  const handleNextImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (images.length > 1) {
      setCurrentImageIndex((prev) => (prev + 1) % images.length);
    }
  };

  const handlePrevImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (images.length > 1) {
      setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      {currentImage && (
        <div className="relative w-full h-48 bg-gray-100">
          <img
            src={currentImage}
            alt={product.title}
            className="w-full h-full object-cover"
          />
          {images.length > 1 && (
            <>
              <button
                onClick={handlePrevImage}
                className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 text-white rounded-full p-1 hover:bg-black/70 transition-colors"
                aria-label="Previous image"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <button
                onClick={handleNextImage}
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 text-white rounded-full p-1 hover:bg-black/70 transition-colors"
                aria-label="Next image"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
              <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                {images.map((_, index) => (
                  <button
                    key={index}
                    onClick={(e) => {
                      e.stopPropagation();
                      setCurrentImageIndex(index);
                    }}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      index === currentImageIndex ? 'bg-white' : 'bg-white/50'
                    }`}
                    aria-label={`Go to image ${index + 1}`}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2 mb-2">
          <h3 className="text-lg font-semibold text-gray-900 flex-1">{product.title}</h3>
          {product.category && (
            <span className="px-2 py-1 text-xs font-medium bg-indigo-100 text-indigo-800 rounded-full whitespace-nowrap">
              {product.category}
            </span>
          )}
        </div>
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
