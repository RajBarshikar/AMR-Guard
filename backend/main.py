from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.medication import router as medication_router

app = FastAPI(
    title="Snap & Drop API",
    description="Backend API for antimicrobial resistance medication disposal",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(medication_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Snap & Drop API is running", "version": "1.0.0"}
