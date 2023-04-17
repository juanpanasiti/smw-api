from fastapi import HTTPException


class BaseHTTPException(HTTPException):
    description: str
    status_code: int

    def __init__(self, message: str) -> None:
        super().__init__(status_code=self.status_code, detail=message)

    @classmethod
    def dict(cls) -> dict:
        return {'description': cls.description}
