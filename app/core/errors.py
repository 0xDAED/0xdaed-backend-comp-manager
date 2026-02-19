from fastapi import HTTPException

class DomainError(Exception):
    code: str = "domain_error"
    message: str = "Domain error"

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)
        self.message = message or self.message

class NotFound(DomainError):
    code = "not_found"
    message = "Not found"

class Forbidden(DomainError):
    code = "forbidden"
    message = "Forbidden"

def to_http(exc: DomainError) -> HTTPException:
    status = 404 if isinstance(exc, NotFound) else 403 if isinstance(exc, Forbidden) else 400
    return HTTPException(status_code=status, detail={"code": exc.code, "message": exc.message})
