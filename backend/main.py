from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import users
from backend.errors import register_exception_handlers

app = FastAPI(
    title="fyll-platoform API",
    description="Refactored backend: modular FastAPI app (users, auth, notifications).",
    version="0.1.0",
)

# CORS - allow local dev and frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])

# Register error handlers
register_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
