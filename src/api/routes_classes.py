import json
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse

from src.core.redis import redis_client

logger = structlog.get_logger()


class IdempotentRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
                return await original_route_handler(request)

            idempotency_key = request.headers.get("Idempotency-Key")
            if not idempotency_key:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": {
                            "code": "MISSING_IDEMPOTENCY_KEY",
                            "message": "Idempotency-Key header is required for mutating requests.",
                            "details": {},
                        },
                    },
                )

            cache_key = f"idempotency:{idempotency_key}"

            cached_response = await redis_client.get(cache_key)
            if cached_response:
                logger.info("idempotency_cache_hit", idempotency_key=idempotency_key)
                data = json.loads(cached_response)
                return JSONResponse(status_code=data.get("status_code", 200), content=data.get("content", {}))

            # Proceed with the actual request
            response: Response = await original_route_handler(request)

            # We only cache successful responses (or specific expected ones)
            if 200 <= response.status_code < 300 and hasattr(response, "body"):
                try:
                    content = json.loads(response.body)
                    await redis_client.setex(
                        cache_key,
                        5,  # 5 seconds sliding window
                        json.dumps({"status_code": response.status_code, "content": content}),
                    )
                except json.JSONDecodeError:
                    pass  # If it's not JSON, we don't cache it for idempotency in this implementation

            return response

        return custom_route_handler
