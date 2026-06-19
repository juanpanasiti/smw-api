import json

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from src.core.redis import redis_client

logger = structlog.get_logger()

class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return await call_next(request)

        # Exclude login route from idempotency requirement
        if request.url.path.endswith("/auth/login"):
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            if request.method == "POST":
                # Some implementations strictly require the key. For now we will just log a warning
                # or we could enforce it. Architecture says "mandate".
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": {
                            "code": "MISSING_IDEMPOTENCY_KEY",
                            "message": "Idempotency-Key header is required for mutating requests.",
                            "details": {}
                        }
                    }
                )
            else:
                return await call_next(request)

        # Scoped by user_id if possible, but at this level we might not have it parsed yet,
        # so we rely on the UUID uniqueness of the idempotency key.
        cache_key = f"idempotency:{idempotency_key}"

        # Check if already processed
        cached_response = await redis_client.get(cache_key)
        if cached_response:
            logger.info("idempotency_cache_hit", idempotency_key=idempotency_key)
            data = json.loads(cached_response)
            return JSONResponse(
                status_code=data.get("status_code", 200),
                content=data.get("content", {})
            )

        # Process the request
        response = await call_next(request)

        # We only cache successful responses (or based on business logic)
        # To cache the body we need to consume it, but in Starlette consuming response body in middleware is tricky.
        # A proper implementation often uses a decorator on the route instead of global middleware,
        # or consumes the body via streaming.
        # For this skeleton, we will implement a basic lock-only or pass-through if we can't read the body easily.
        # A full response caching middleware requires reading the body stream.

        # For simplicity in this architecture step, we'll cache a generic success or
        # use a route-level dependency in the future for exact payload caching.
        # We'll just set the key to prevent immediate double-clicks (5 seconds lock).

        await redis_client.setex(cache_key, 5, json.dumps({
            "status_code": response.status_code,
            "content": {"message": "Request processed. (Cached response body placeholder)"}
        }))

        return response
