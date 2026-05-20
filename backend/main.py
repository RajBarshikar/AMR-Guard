import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

from routes.medication import router as medication_router
from routes.rewards    import router as rewards_router
from routes.community  import router as community_router
from routes.pharmacy   import router as pharmacy_router

# ---------------------------------------------------------------------------
# Rate limiting (slowapi)
# ---------------------------------------------------------------------------
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
    _rate_limiting = True
except Exception:
    limiter = None
    _rate_limiting = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[AMR-Guard] Starting up...")
    yield
    print("[AMR-Guard] Shutting down...")


app = FastAPI(
    title="AMR-Guard API",
    description="Backend API for antimicrobial resistance medication disposal — AMR-Guard",
    version="2.0.0",
    lifespan=lifespan,
)

if _rate_limiting:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(medication_router, prefix="/api/v1", tags=["Medication"])
app.include_router(rewards_router,    prefix="/api/v1", tags=["Rewards"])
app.include_router(community_router,  prefix="/api/v1", tags=["Community"])
app.include_router(pharmacy_router,   prefix="/api/v1", tags=["Pharmacy"])


# ---------------------------------------------------------------------------
# Core endpoints
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "AMR-Guard API is running",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check — used by deployment platforms."""
    from firebase_client import _firebase_available
    return {
        "status": "healthy",
        "version": "2.0.0",
        "firebase_connected": _firebase_available,
        "rate_limiting": _rate_limiting,
    }


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[AMR-Guard] Unhandled error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "detail": str(exc)},
    )
