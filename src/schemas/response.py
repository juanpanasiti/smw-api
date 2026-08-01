from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}


class StandardResponse[T](BaseModel):
    success: bool
    data: T | None = None
    error: ErrorDetail | None = None
