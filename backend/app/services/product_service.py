"""Product service for business logic."""
from sqlalchemy.orm import Session
from app.models import Product
from app.schemas import ProductCreate, ProductUpdate
from app.services.stripe_sync import sync_product_to_stripe


def format_price(amount: int, currency: str = "usd") -> str:
    """Format price amount to display string."""
    major_units = amount / 100
    if currency.lower() == "usd":
        return f"${major_units:.2f}"
    elif currency.lower() == "eur":
        return f"€{major_units:.2f}"
    else:
        return f"{major_units:.2f} {currency.upper()}"


def create_product(db: Session, product_data: ProductCreate) -> Product:
    """Create a new product and sync to Stripe."""
    product = Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Sync to Stripe
    sync_product_to_stripe(db, product)
    
    return product


def update_product(db: Session, product_id: int, product_data: ProductUpdate) -> Product:
    """Update a product and sync changes to Stripe."""
    product = db.query(Product).filter(Product.id == product_id, Product.deleted_at.is_(None)).first()
    if not product:
        raise ValueError("Product not found")
    
    # Track if price changed
    price_changed = (
        product_data.current_price_amount is not None and
        product_data.current_price_amount != product.current_price_amount
    )
    
    # Update fields
    update_dict = product_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    # Sync to Stripe if any changes
    sync_product_to_stripe(db, product)
    
    return product


def delete_product(db: Session, product_id: int) -> bool:
    """Soft delete a product."""
    product = db.query(Product).filter(Product.id == product_id, Product.deleted_at.is_(None)).first()
    if not product:
        return False
    
    from datetime import datetime
    product.deleted_at = datetime.utcnow()
    db.commit()
    return True


def get_products(db: Session, published_only: bool = False) -> list[Product]:
    """Get products, optionally filtered by published status."""
    query = db.query(Product).filter(Product.deleted_at.is_(None))
    if published_only:
        query = query.filter(Product.published == True)
    return query.all()


def get_product(db: Session, product_id: int) -> Product:
    """Get a single product by ID."""
    return db.query(Product).filter(Product.id == product_id, Product.deleted_at.is_(None)).first()
