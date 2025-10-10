from fastapi import FastAPI  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware 
from app.api.v1.routers import router as v1_router


def create_app() -> FastAPI:
    _app = FastAPI(title="aequatio", version="1.0.0")
        # Enable CORS for the Vite dev server (adjust origins as needed)
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # change to ["*"] for all origins (dev only)
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ) 



    _app.include_router(v1_router, prefix="/api/v1")
    return _app


# Export app for ASGI servers (uvicorn/gunicorn etc.)
app = create_app()


if __name__ == "__main__":
    # Local import to avoid adding uvicorn as a hard dependency for static
    # linters. Run with: python main.py
    import importlib

    uvicorn = importlib.import_module("uvicorn")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
