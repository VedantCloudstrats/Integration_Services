from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError


# ─────────────────────────────────────────────
# Custom exception classes
# ─────────────────────────────────────────────

class AppBaseException(Exception):
    """Base class for all application exceptions."""
    status_code: int = 500
    error: str = "Internal Server Error"

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ItemNotFoundError(AppBaseException):
    status_code = 404
    error = "Not Found"


class DuplicateEntryError(AppBaseException):
    status_code = 409
    error = "Conflict"


class DatabaseError(AppBaseException):
    status_code = 503
    error = "Database Unavailable"


class AuthorizationError(AppBaseException):
    status_code = 401
    error = "Unauthorized"


class ForbiddenError(AppBaseException):
    status_code = 403
    error = "Forbidden"


class BadRequestError(AppBaseException):
    status_code = 400
    error = "Bad Request"


# ─────────────────────────────────────────────
# Standard error response builder
# ─────────────────────────────────────────────

def _error_response(status_code: int, error: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status_code": status_code,
            "error": error,
            "detail": detail,
        },
    )


# ─────────────────────────────────────────────
# Exception handlers — register on FastAPI app
# ─────────────────────────────────────────────

async def app_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    return _error_response(exc.status_code, exc.error, exc.detail)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    error_map = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }
    error = error_map.get(exc.status_code, "HTTP Error")
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return _error_response(exc.status_code, error, detail)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Flatten all field errors into a human-readable string
    errors = []
    for err in exc.errors():
        field = " → ".join(str(loc) for loc in err["loc"])
        msg = err["msg"]
        errors.append(f"{field}: {msg}")
    detail = "; ".join(errors)
    return _error_response(422, "Validation Error", detail)


async def pydantic_validation_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    errors = [f"{' → '.join(str(l) for l in e['loc'])}: {e['msg']}" for e in exc.errors()]
    return _error_response(422, "Validation Error", "; ".join(errors))


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return _error_response(500, "Internal Server Error", f"An unexpected error occurred: {type(exc).__name__}")
