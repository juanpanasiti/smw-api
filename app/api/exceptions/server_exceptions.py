# status.HTTP_500_INTERNAL_SERVER_ERROR
# status.HTTP_501_NOT_IMPLEMENTED
# status.HTTP_503_SERVICE_UNAVAILABLE
from .base_exception import BaseHTTPException


class InternalServerError(BaseHTTPException):
    description = 'Unhadled error.'
    status_code = 500


class NotImplemented(BaseHTTPException):
    description = 'Service not implemented yet.'
    status_code = 501


class ServiceUnavailable(BaseHTTPException):
    description = 'Service is not available.'
    status_code = 503
