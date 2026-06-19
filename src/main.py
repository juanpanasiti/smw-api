from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware import IdempotencyMiddleware
from src.core.config import settings
from src.core.logger import setup_logging
from src.routes.auth_routes import router as auth_router

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Idempotency Middleware
app.add_middleware(IdempotencyMiddleware)

# Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
