# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a minimal e-commerce demo application that integrates Stripe for payment processing. The application serves as the catalog source of truth, with Stripe handling checkout, payments, and price objects. Admin can manage products without authentication, and changes automatically sync to Stripe.

**Tech Stack:**
- **Backend**: FastAPI + Supabase (PostgreSQL) + Stripe API
- **Frontend**: React + TypeScript + Vite + Tailwind CSS

## Development Commands

### Backend (Python 3.9+)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev          # Development server (localhost:3000)
npm run build        # Production build (runs tsc && vite build)
npm run preview      # Preview production build
npm run lint         # Run ESLint
```

### Stripe Webhook Testing
```bash
stripe login
stripe listen --forward-to localhost:8000/stripe/webhook
```

## Architecture

The application follows a microservices-style architecture:

```
Frontend (React)  -->  Backend (FastAPI)  -->  Stripe API
                              |
                              v
                        Supabase (PostgreSQL)
```

**Key architectural patterns:**
- The application (backend DB) is the source of truth for products; Stripe is kept in sync via background operations
- Stripe Checkout handles payment flow; webhook confirms order completion
- Admin operations have no authentication (demo purposes)
- Soft delete is used for products to preserve order history

### Backend Structure (`/backend/app/`)
- `main.py` - FastAPI application entry point with CORS and route configuration
- `config.py` - Environment-based settings (Supabase, Stripe, frontend URL)
- `database.py` - Supabase client initialization
- `models.py` - SQLAlchemy models for products, orders, order_items, stripe_events
- `schemas.py` - Pydantic schemas for request/response validation
- `stripe_client.py` - Stripe API wrapper
- `api/` - Endpoint modules: `products.py`, `checkout.py`, `orders.py`, `webhooks.py`
- `services/` - Business logic: `product_service.py`, `stripe_sync.py`, `order_service.py`

### Frontend Structure (`/frontend/src/`)
- `pages/` - Page components: `Home.tsx` (storefront), `Cart.tsx`, `Admin.tsx`, `Success.tsx`, `Cancel.tsx`, `AdminProductEdit.tsx`
- `components/` - Reusable UI components
- `services/` - API client
- `contexts/` - React contexts (e.g., cart state)

## Environment Variables

**Backend (`backend/.env`):**
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
FRONTEND_URL=http://localhost:3000
```

**Frontend (`frontend/.env`):**
```
VITE_API_URL=http://localhost:8000
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

## API Endpoints

**Products:**
- `GET /products` - Published products for storefront
- `GET /products/admin` - All products including unpublished (admin)
- `POST /admin/products` - Create product (syncs to Stripe)
- `PUT /admin/products/{id}` - Update product (syncs to Stripe)
- `DELETE /admin/products/{id}` - Soft delete product
- `POST /admin/products/{id}/resync` - Retry failed Stripe sync

**Checkout:**
- `POST /checkout/session` - Create Stripe Checkout Session

**Orders:**
- `GET /orders/{id}` - Get order by ID
- `GET /orders/by-session/{session_id}` - Get order by Stripe session ID

**Webhooks:**
- `POST /stripe/webhook` - Handle Stripe events (checkout.session.completed)

## Database Schema

Located in `backend/supabase_schema.sql`. Key tables:
- `products` - Product catalog with Stripe integration fields (stripe_product_id, stripe_price_id, sync_status)
- `orders` - Order tracking with Stripe session IDs
- `order_items` - Individual items in each order
- `stripe_events` - Webhook idempotency tracking (prevents duplicate processing)

## Stripe Sync Flow

When admin creates/updates a product:
1. Product saved to database with `sync_status='pending'`
2. Background sync creates/updates Stripe Product and Price objects
3. Stripe IDs stored back in database
4. `sync_status` updated to 'success' or 'failed'
5. Failed syncs can be retried via `/admin/products/{id}/resync`
