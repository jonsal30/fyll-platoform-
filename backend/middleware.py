from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional

# Very small idempotency middleware using in-memory store.
# For production: back this with Redis and set TTLs.

from backend import services


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        # Only apply to POST requests
        if request.method == "POST":
            idempotency_key = request.headers.get("Idempotency-Key")
            if idempotency_key:
                stored = services._idempotency_store.get(idempotency_key)
                if stored:
                    # Return stored representation (we keep JSON serializable objects)
                    return Response(content=stored and str(stored), media_type="application/json")

        response = await call_next(request)
        return response


# Request logging middleware can be added similarly; for now we keep simple.
