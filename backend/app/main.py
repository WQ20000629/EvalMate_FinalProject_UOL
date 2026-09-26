# ------------------------------------------------------------------
# File: backend/app/main.py
# Purpose: Starts the FastAPI application and registers its middleware and routes.
# ------------------------------------------------------------------

# Import the libraries needed for the FastAPI app
import threading

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.auth import router as auth_router
from app.api.sessions import router as sessions_router
from app.models.question_generator import QuestionGenerator

# Create the FastAPI app object
app = FastAPI(title="EvalMate", version="1.0.0")

# Allow the frontend to call the API from localhost:5173
# The browser needs an exact origin for auth cookies
# ref: https://fastapi.tiangolo.com/tutorial/cors/
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach all API routers under the /api prefix
app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")


def _warm_up_ollama() -> None:
    """Load the Ollama model in the background so the first real request is faster."""
    try:
        generator = QuestionGenerator()
        requests.post(
            generator.endpoint,
            json={"model": generator.llm_model, "prompt": "Say hello.", "stream": False},
            timeout=180,
        )
    except requests.exceptions.RequestException:
        pass  # Ollama is not running yet, so the model loads on the first real request


# Start the background warm-up when the app starts
@app.on_event("startup")
def warm_up_ollama_on_startup() -> None:
    threading.Thread(target=_warm_up_ollama, daemon=True).start()


@app.get("/")
def ping():
    """Simple health check to confirm the API is running."""
    return {"status": "ok"}
