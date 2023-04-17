from .base_exception import BaseHTTPException


class BadRequest(BaseHTTPException):
    description = 'Something is wrong with the request'
    status_code = 400


class Unauthorized(BaseHTTPException):
    description = 'Must be logged in.'
    status_code = 401


class Forbidden(BaseHTTPException):
    status_code = 403
    description = 'Have no access to this resource.'


class NotFound(BaseHTTPException):
    description = 'Resource not found.'
    status_code = 404


# status.HTTP_422_UNPROCESSABLE_ENTITY
# TODO
