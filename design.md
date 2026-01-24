# Ecommerce Demo with Stripe Integration - Design Document

## Overview

A minimal ecommerce demo application with Stripe integration. The application serves as the catalog source of truth, while Stripe handles checkout, payments, and price objects. Admin can manage products without authentication, and changes automatically sync to Stripe.

---

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Frontend      │         │   Backend       │         │     Stripe      │
│   (React/Vue)   │◄────────┤   (FastAPI)     │◄────────┤   (API)         │
│                 │         │                 │         │                 │
│ - Storefront    │         │ - Product APIs  │         │ - Products      │
│ - Admin Page    │         │ - Checkout API  │         │ - Prices        │
│ - Cart          │         │ - Webhook       │         │ - Checkout      │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                      │
                                      ▼
                            ┌─────────────────┐
                            │   Supabase      │
                            │   (PostgreSQL)  │
                            │                 │
                            │ - Products      │
                            │ - Orders        │
                            │ - Sync Events   │
                            └─────────────────┘
```

---

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Database Client**: Supabase Python client
- **Stripe SDK**: `stripe` Python library
- **Validation**: Pydantic

### Frontend
- **Framework**: React (or Vue.js)
- **UI Library**: Tailwind CSS / shadcn/ui
- **HTTP Client**: Axios / Fetch
- **State Management**: React Context / Zustand (optional)

### Infrastructure
- **Webhook Verification**: Stripe signature verification
- **Environment Variables**: `.env` for secrets

---

## Database Schema

### Product Table

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    images JSONB DEFAULT '[]'::jsonb,  -- Array of image URLs (replaces image_url)
    category VARCHAR(100),  -- New: Product category
    currency VARCHAR(3) NOT NULL DEFAULT 'usd',
    current_price_amount INTEGER NOT NULL,  -- in minor units (cents)
    published BOOLEAN DEFAULT FALSE,
    
    -- Stripe integration fields
    stripe_product_id VARCHAR(255) NULL,
    active_stripe_price_id VARCHAR(255) NULL,
    last_sync_status VARCHAR(50) NULL,  -- 'success', 'failed', 'pending'
    last_sync_at TIMESTAMP NULL,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL  -- soft delete
);

CREATE INDEX idx_products_published ON products(published) WHERE deleted_at IS NULL;
CREATE INDEX idx_products_stripe_product_id ON products(stripe_product_id);
CREATE INDEX idx_products_category ON products(category) WHERE deleted_at IS NULL;
```

### Order Table

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- or UUID
    status VARCHAR(50) NOT NULL DEFAULT 'pending_payment',  -- 'pending_payment', 'paid', 'failed', 'cancelled'
    stripe_checkout_session_id VARCHAR(255) UNIQUE,
    total_amount_snapshot INTEGER NOT NULL,  -- in minor units
    currency VARCHAR(3) NOT NULL DEFAULT 'usd',
    customer_email VARCHAR(255),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_session_id ON orders(stripe_checkout_session_id);
CREATE INDEX idx_orders_status ON orders(status);
```

### Order Item Table

```sql
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    stripe_price_id_used VARCHAR(255) NOT NULL,
    unit_amount_snapshot INTEGER NOT NULL,  -- price at time of checkout
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
```

### Stripe Event Table (Idempotency)

```sql
CREATE TABLE stripe_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stripe_event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_stripe_events_event_id ON stripe_events(stripe_event_id);
```

---

## API Endpoints

### Product APIs

#### `GET /products`
**Description**: Get published products for storefront

**Query Parameters**:
- `category` (optional): Filter by category
- `search` (optional): Search in title and description

**Response**:
```json
{
  "products": [
    {
      "id": 1,
      "title": "Product Name",
      "description": "Description",
      "image_url": "https://...",  // Backward compatibility (first image)
      "images": ["https://...", "https://..."],  // Multiple images
      "category": "Electronics",  // New field
      "currency": "usd",
      "current_price_amount": 1999,
      "formatted_price": "$19.99"
    }
  ]
}
```

#### `GET /admin/products`
**Description**: Get all products (including unpublished) for admin

**Query Parameters**:
- `category` (optional): Filter by category
- `search` (optional): Search in title and description

**Response**: Same as above, but includes `published`, `stripe_product_id`, `active_stripe_price_id`, `last_sync_status`, `last_sync_at`

#### `POST /admin/products`
**Description**: Create a new product

**Request**:
```json
{
  "title": "Product Name",
  "description": "Description",
  "images": ["https://...", "https://..."],  // Multiple images
  "category": "Electronics",  // Optional category
  "currency": "usd",
  "current_price_amount": 1999,
  "published": true
}
```

**Response**: Created product with Stripe sync status

**Behavior**:
- Creates product in DB
- Creates Stripe Product (if not exists)
- Creates Stripe Price
- Updates `stripe_product_id`, `active_stripe_price_id`, `last_sync_status`

#### `PUT /admin/products/{id}`
**Description**: Update a product

**Request**: Same as POST (all fields optional)

**Behavior**:
- Updates product in DB
- If non-price fields changed → updates Stripe Product
- If price changed → creates new Stripe Price, sets as active, optionally deactivates old price
- Updates sync status

#### `DELETE /admin/products/{id}`
**Description**: Soft delete a product

**Response**: `{"success": true}`

**Behavior**: Sets `deleted_at` timestamp (doesn't delete from Stripe)

---

### Checkout APIs

#### `POST /checkout/session`
**Description**: Create Stripe Checkout Session

**Request**:
```json
{
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    }
  ],
  "success_url": "https://yourapp.com/success?session_id={CHECKOUT_SESSION_ID}",
  "cancel_url": "https://yourapp.com/cancel"
}
```

**Response**:
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_test_..."
}
```

**Behavior**:
1. Validate products exist and are published
2. Load active Stripe Price IDs from DB
3. Create Order in DB with status `pending_payment`
4. Create Stripe Checkout Session with line_items
5. Store `stripe_checkout_session_id` in Order
6. Return checkout URL

#### `GET /orders/{id}`
**Description**: Get order by ID

**Response**:
```json
{
  "id": 1,
  "status": "paid",
  "total_amount_snapshot": 3998,
  "currency": "usd",
  "customer_email": "customer@example.com",
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "unit_amount_snapshot": 1999
    }
  ],
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### `GET /orders/by-session/{session_id}`
**Description**: Get order by Stripe Checkout Session ID

**Response**: Same as `GET /orders/{id}`

---

### Webhook API

#### `POST /stripe/webhook`
**Description**: Handle Stripe webhook events

**Headers**:
- `Stripe-Signature`: Stripe signature for verification

**Behavior**:
1. Verify Stripe signature
2. Parse event
3. Check idempotency (query `stripe_events` table)
4. If already processed → return 200 (idempotent)
5. Process event:
   - `checkout.session.completed` → update order status to `paid`
6. Store event in `stripe_events` table
7. Return 200

**Event Handling**:
```python
if event.type == 'checkout.session.completed':
    session = event.data.object
    order = get_order_by_session_id(session.id)
    if order and order.status == 'pending_payment':
        order.status = 'paid'
        order.customer_email = session.customer_details.email
        db.commit()
```

---

## Frontend Components

### Storefront

#### Product List Page (`/`)
- Display grid/list of published products
- **Search bar**: Search products by title and description (debounced)
- **Category filter**: Filter products by category with buttons
- Product card shows: images (carousel if multiple), title, category badge, price, "Add to Cart" button
- Link to product details (optional)

#### Product Details Page (`/products/{id}`) (Optional)
- Full product information
- Add to cart with quantity selector

#### Cart Page (`/cart`)
- List of cart items with quantities
- Update quantity / remove items
- Display total
- "Checkout" button

#### Success Page (`/success`)
- Thank you message
- Order confirmation details
- Link to order details

#### Cancel Page (`/cancel`)
- Message that checkout was cancelled
- Link back to cart

### Admin Page

#### Admin Product List (`/admin`)
- Table/list of all products (published + unpublished)
- Product card shows:
  - Product details (title, description, image, price)
  - Published status toggle
  - Stripe status:
    - Stripe Product ID
    - Active Stripe Price ID
    - Last sync status (success/failed/pending)
    - Last sync timestamp
  - Actions:
    - Edit button
    - Delete button
    - Resync button (retries Stripe sync)

#### Create/Edit Product Form (`/admin/products/new`, `/admin/products/{id}/edit`)
- Form fields:
  - Title (required)
  - Description (textarea)
  - Category (text input, optional)
  - Images (multiple URL inputs with add/remove functionality)
  - Currency (dropdown: USD, EUR, etc.)
  - Price (number input, in major units)
  - Published (toggle)
- Buttons:
  - "Save" (saves to DB, auto-syncs to Stripe)
  - "Cancel"

---

## Stripe Integration Flow

### Product Creation Flow

```
Admin creates product
    ↓
POST /admin/products
    ↓
Backend creates product in DB
    ↓
Backend calls Stripe API:
    - Create Product (if stripe_product_id is null)
    - Create Price
    ↓
Backend updates DB:
    - stripe_product_id
    - active_stripe_price_id
    - last_sync_status = 'success'
    - last_sync_at = now()
    ↓
Response to admin with sync status
```

### Price Update Flow

```
Admin changes price
    ↓
PUT /admin/products/{id} with new price
    ↓
Backend detects price change
    ↓
Backend calls Stripe API:
    - Create NEW Price (Stripe doesn't allow price updates)
    - Optionally deactivate old price
    ↓
Backend updates DB:
    - current_price_amount = new price
    - active_stripe_price_id = new price ID
    - last_sync_status = 'success'
    ↓
Old price ID is no longer used for new checkouts
```

### Checkout Flow

```
Customer clicks "Checkout"
    ↓
POST /checkout/session with cart items
    ↓
Backend:
    1. Validates products (published, exist)
    2. Loads active_stripe_price_id for each product
    3. Creates Order in DB (pending_payment)
    4. Creates Stripe Checkout Session with line_items
    5. Stores session_id in Order
    ↓
Returns checkout_url
    ↓
Frontend redirects to Stripe Checkout
    ↓
Customer completes payment on Stripe
    ↓
Stripe sends webhook: checkout.session.completed
    ↓
Backend webhook handler:
    1. Verifies signature
    2. Checks idempotency
    3. Updates Order status to 'paid'
    ↓
Customer redirected to /success page
```

---

## File Structure

```
stripe_demo/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Config (env vars)
│   │   ├── database.py             # DB connection
│   │   ├── models.py                # SQLAlchemy models
│   │   ├── schemas.py               # Pydantic schemas
│   │   ├── stripe_client.py        # Stripe API wrapper
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── products.py         # Product endpoints
│   │   │   ├── checkout.py         # Checkout endpoints
│   │   │   ├── orders.py           # Order endpoints
│   │   │   └── webhooks.py         # Webhook handler
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── product_service.py  # Product business logic
│   │       ├── stripe_sync.py      # Stripe sync logic
│   │       └── order_service.py   # Order business logic
│   │
│   ├── alembic/                    # DB migrations (optional)
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ProductCard.tsx
│   │   │   ├── Cart.tsx
│   │   │   ├── AdminProductList.tsx
│   │   │   └── ProductForm.tsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Home.tsx            # Storefront
│   │   │   ├── Cart.tsx
│   │   │   ├── Success.tsx
│   │   │   ├── Cancel.tsx
│   │   │   ├── Admin.tsx
│   │   │   └── AdminProductEdit.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useCart.ts
│   │   │   └── useProducts.ts
│   │   │
│   │   ├── services/
│   │   │   └── api.ts              # API client
│   │   │
│   │   └── App.tsx
│   │
│   ├── package.json
│   └── vite.config.ts (or similar)
│
├── README.md
├── design.md
└── docker-compose.yml (optional)
```

---

## Environment Variables

```bash
# Backend
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
FRONTEND_URL=http://localhost:3000

# Frontend
VITE_API_URL=http://localhost:8000
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

---

## Security Considerations

1. **Admin Page**: No authentication (as per requirements), but consider:
   - Rate limiting
   - IP whitelist (optional)
   - CSRF protection

2. **Webhook Security**:
   - Always verify Stripe signature
   - Use `STRIPE_WEBHOOK_SECRET` from Stripe dashboard

3. **API Security**:
   - CORS configuration
   - Input validation (Pydantic)
   - SQL injection prevention (SQLAlchemy ORM)

4. **Stripe Keys**:
   - Never expose secret keys in frontend
   - Use environment variables
   - Rotate keys regularly

---

## Error Handling

### Stripe Sync Failures
- Store error in `last_sync_status` (e.g., "failed: insufficient funds")
- Provide "Resync" button in admin UI
- Log errors for debugging

### Checkout Failures
- Handle Stripe API errors gracefully
- Return user-friendly error messages
- Log errors server-side

### Webhook Failures
- Retry logic (Stripe retries automatically)
- Idempotency prevents double-processing
- Log failed webhooks for manual review

---

## Testing Strategy

### Unit Tests
- Product service logic
- Stripe sync logic
- Price update logic

### Integration Tests
- API endpoints
- Stripe API calls (use test mode)
- Webhook handling

### E2E Tests
- Admin creates product → Stripe sync
- Admin updates price → new Price created
- Customer checkout → order created → webhook updates order

---

## Proof Points (Demo Checklist)

- [ ] Admin creates product → Stripe Product + Price created
- [ ] Admin changes price → new Stripe Price created, active price updated
- [ ] Checkout uses Stripe Price IDs (server-side validation)
- [ ] Webhook confirms payment and updates order status
- [ ] Idempotency prevents double-processing
- [ ] Resync button works for failed syncs
- [ ] Soft delete works (products hidden but not deleted from Stripe)

---

## Future Enhancements (Out of Scope)

- User authentication
- Inventory management
- Order history for customers
- Admin dashboard analytics
- Multiple currencies with conversion
- Discount codes
- Shipping integration
- Email notifications

---

## Implementation Phases

### Phase 1: Core Setup
1. FastAPI backend structure
2. Database models and migrations
3. Basic product CRUD APIs
4. Stripe client setup

### Phase 2: Stripe Integration
1. Product → Stripe sync
2. Price update logic
3. Sync status tracking

### Phase 3: Checkout
1. Checkout session creation
2. Order creation
3. Frontend cart + checkout flow

### Phase 4: Webhooks
1. Webhook endpoint
2. Event handling
3. Idempotency

### Phase 5: Admin UI
1. Admin product list
2. Create/edit forms
3. Sync status display
4. Resync functionality

### Phase 6: Storefront
1. Product listing
2. Cart functionality
3. Success/cancel pages

---

## Notes

- **Price Updates**: Stripe doesn't allow updating prices. Always create new Price objects.
- **Idempotency**: Critical for webhooks. Always check `stripe_events` table.
- **Soft Delete**: Recommended to preserve order history and Stripe references.
- **Sync Status**: Helps admin understand Stripe sync state and debug issues.
- **Test Mode**: Use Stripe test mode during development.
