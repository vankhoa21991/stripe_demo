/** Products hook for fetching products */
import { useState, useEffect } from 'react';
import { getProducts, Product } from '../services/api';

interface UseProductsOptions {
  category?: string;
  search?: string;
}

export const useProducts = (options?: UseProductsOptions) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        const data = await getProducts(options?.category, options?.search);
        setProducts(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch products');
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [options?.category, options?.search]);

  return { products, loading, error };
};
