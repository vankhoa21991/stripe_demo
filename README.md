# Ecommerce Demo with Stripe Integration

A minimal ecommerce demo application with Stripe integration. The application serves as the catalog source of truth, while Stripe handles checkout, payments, and price objects. Admin can manage products without authentication, and changes automatically sync to Stripe.

## Features

- **Product Management**: Admin can create, update, and delete products
- **Stripe Integration**: Automatic sync of products and prices to Stripe
- **Checkout Flow**: Stripe Checkout for secure payment processing
- **Order Tracking**: Webhook-based order status updates
- **Storefront**: Customer-facing product catalog and shopping cart

## Architecture

- **Backend**: FastAPI with SQLAlchemy
- **Frontend**: React with TypeScript and Tailwind CSS
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Payment**: Stripe Checkout

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- Stripe account (test mode)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
# Database
DATABASE_URL=sqlite:///./app.db

# Stripe (get these from your Stripe dashboard)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Frontend
FRONTEND_URL=http://localhost:3000
```

5. Run the backend:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file:
```bash
VITE_API_URL=http://localhost:8000
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

4. Run the frontend:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Stripe Webhook Setup

1. Install Stripe CLI: https://stripe.com/docs/stripe-cli

2. Login to Stripe:
```bash
stripe login
```

3. Forward webhooks to your local server:
```bash
stripe listen --forward-to localhost:8000/stripe/webhook
```

4. Copy the webhook signing secret (starts with `whsec_`) and add it to your backend `.env` file.

## Usage

### Admin Flow

1. Navigate to `/admin` to manage products
2. Click "Create Product" to add a new product
3. Fill in product details and save
4. The product will automatically sync to Stripe
5. Use the "Resync" button if sync fails

### Customer Flow

1. Browse products on the homepage
2. Add products to cart
3. Click "Checkout" to proceed to Stripe Checkout
4. Complete payment on Stripe
5. Redirected to success page with order confirmation

## API Endpoints

### Products
- `GET /products` - Get published products (storefront)
- `GET /products/admin` - Get all products (admin)
- `POST /products/admin` - Create product
- `PUT /products/admin/{id}` - Update product
- `DELETE /products/admin/{id}` - Delete product
- `POST /products/admin/{id}/resync` - Resync product to Stripe

### Checkout
- `POST /checkout/session` - Create Stripe Checkout Session

### Orders
- `GET /orders/{id}` - Get order by ID
- `GET /orders/by-session/{session_id}` - Get order by Stripe session ID

### Webhooks
- `POST /stripe/webhook` - Stripe webhook handler

## Testing

Use Stripe test mode for development. Test card numbers:
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`

## Project Structure

```
stripe_demo/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── services/     # Business logic
│   │   ├── models.py     # Database models
│   │   ├── schemas.py    # Pydantic schemas
│   │   ├── database.py   # DB connection
│   │   ├── config.py     # Configuration
│   │   ├── stripe_client.py  # Stripe API wrapper
│   │   └── main.py       # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   ├── services/     # API client
│   │   └── App.tsx       # Main app
│   └── package.json
└── README.md
```

## Security Notes

- Admin page has no authentication (as per design requirements)
- Webhook signature verification is implemented
- Stripe secret keys should never be exposed to frontend
- Use environment variables for all secrets

## License

See LICENSE file.
