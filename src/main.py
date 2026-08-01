from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logger import setup_logging
from src.routes.account_routes import router as account_router
from src.routes.auth_routes import router as auth_router
from src.routes.bill_routes import router as bill_router
from src.routes.category_routes import router as category_router
from src.routes.expense_routes import router as expense_router
from src.routes.projection_routes import router as projection_router

setup_logging()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, openapi_url=f"{settings.API_V1_STR}/openapi.json")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(category_router, prefix=settings.API_V1_STR)
app.include_router(account_router, prefix=settings.API_V1_STR)
app.include_router(expense_router, prefix=settings.API_V1_STR)
app.include_router(bill_router, prefix=settings.API_V1_STR)
app.include_router(projection_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
