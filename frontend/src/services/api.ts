/** API client for backend communication */
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Product {
  id: number;
  title: string;
  description: string | null;
  image_url: string | null;
  currency: string;
  current_price_amount: number;
  formatted_price: string;
  published?: boolean;
  stripe_product_id?: string | null;
  active_stripe_price_id?: string | null;
  last_sync_status?: string | null;
  last_sync_at?: string | null;
}

export interface CheckoutItem {
  product_id: number;
  quantity: number;
}

export interface CheckoutSessionRequest {
  items: CheckoutItem[];
  success_url: string;
  cancel_url: string;
}

export interface CheckoutSessionResponse {
  checkout_url: string;
  session_id: string;
}

export interface Order {
  id: number;
  status: string;
  total_amount_snapshot: number;
  currency: string;
  customer_email: string | null;
  items: Array<{
    product_id: number;
    quantity: number;
    unit_amount_snapshot: number;
  }>;
  created_at: string;
}

// Product APIs
export const getProducts = async (): Promise<Product[]> => {
  const response = await api.get<{ products: Product[] }>('/products');
  return response.data.products;
};

export const getAdminProducts = async (): Promise<Product[]> => {
  const response = await api.get<Product[]>('/products/admin');
  return response.data;
};

export const createProduct = async (product: Partial<Product>): Promise<Product> => {
  const response = await api.post<Product>('/products/admin', product);
  return response.data;
};

export const updateProduct = async (id: number, product: Partial<Product>): Promise<Product> => {
  const response = await api.put<Product>(`/products/admin/${id}`, product);
  return response.data;
};

export const deleteProduct = async (id: number): Promise<void> => {
  await api.delete(`/products/admin/${id}`);
};

export const resyncProduct = async (id: number): Promise<void> => {
  await api.post(`/products/admin/${id}/resync`);
};

// Checkout APIs
export const createCheckoutSession = async (
  request: CheckoutSessionRequest
): Promise<CheckoutSessionResponse> => {
  const response = await api.post<CheckoutSessionResponse>('/checkout/session', request);
  return response.data;
};

// Order APIs
export const getOrder = async (id: number): Promise<Order> => {
  const response = await api.get<Order>(`/orders/${id}`);
  return response.data;
};

export const getOrderBySession = async (sessionId: string): Promise<Order> => {
  const response = await api.get<Order>(`/orders/by-session/${sessionId}`);
  return response.data;
};
