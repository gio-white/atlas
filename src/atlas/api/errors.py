from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.services import AlreadyExistsError, NotFoundError, ValidationError


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundError, _json_error(404))
    app.add_exception_handler(AlreadyExistsError, _json_error(409))
    app.add_exception_handler(ValidationError, _json_error(400))


def _json_error(status_code: int):
    async def handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler
