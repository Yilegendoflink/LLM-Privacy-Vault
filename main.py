import logging
from fastapi import FastAPI
from dotenv import load_dotenv
from src.api.routes import router as api_router
from src.api.middleware import AuditLoggingMiddleware

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="LLM-Privacy-Vault",
    description="A lightweight privacy-preserving gateway compatible with OpenAI API format.",
    version="1.0.0",
)

# Add middleware
app.add_middleware(AuditLoggingMiddleware)

# Include routers
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
