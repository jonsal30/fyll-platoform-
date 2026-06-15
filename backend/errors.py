from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from backend.schemas import ProblemDetails


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        problem = ProblemDetails(
            type="about:blank",
            title=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            status=exc.status_code,
            detail=str(exc.detail),
            instance=str(request.url),
        )
        return JSONResponse(status_code=exc.status_code, content=problem.dict())

    # Generic handler
    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc: Exception):
        problem = ProblemDetails(
            type="about:blank",
            title="Internal Server Error",
            status=500,
            detail=str(exc),
            instance=str(request.url),
        )
        return JSONResponse(status_code=500, content=problem.dict())
