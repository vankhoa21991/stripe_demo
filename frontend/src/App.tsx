import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import Cart from './pages/Cart';
import Success from './pages/Success';
import Cancel from './pages/Cancel';
import Admin from './pages/Admin';
import AdminProductEdit from './pages/AdminProductEdit';
import { CartProvider, useCartContext } from './contexts/CartContext';

function AppNav() {
  const { getItemCount } = useCartContext();

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <Link to="/" className="flex items-center px-2 py-2 text-xl font-bold text-gray-900">
                Ecommerce Demo
              </Link>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link
                  to="/"
                  className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 hover:text-gray-700"
                >
                  Store
                </Link>
                <Link
                  to="/admin"
                  className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 hover:text-gray-700"
                >
                  Admin
                </Link>
              </div>
            </div>
            <div className="flex items-center">
              <Link
                to="/cart"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
              >
                Cart ({getItemCount()})
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/cart" element={<Cart />} />
        <Route path="/success" element={<Success />} />
        <Route path="/cancel" element={<Cancel />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/admin/products/new" element={<AdminProductEdit />} />
        <Route path="/admin/products/:id/edit" element={<AdminProductEdit />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <Router>
      <CartProvider>
        <AppNav />
      </CartProvider>
    </Router>
  );
}

export default App;
