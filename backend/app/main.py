"""FastAPI application main file."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import products, checkout, orders, webhooks

app = FastAPI(title="Ecommerce Demo API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router)
app.include_router(checkout.router)
app.include_router(orders.router)
app.include_router(webhooks.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Ecommerce Demo API"}
