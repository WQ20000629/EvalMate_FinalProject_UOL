# Import necessary libraries
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

# Create the FastAPI application instance
app = FastAPI(title="AI Interview Evaluator", version="1.0.0")

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all API routes defined in routes.py under the /api prefix
app.include_router(router, prefix="/api")

@app.get("/")
def ping():
    """
    Simple health check endpoint.
    Returns:
        dict: Basic status message to confirm the API is running.
    """
    return {"status": "ok"}
