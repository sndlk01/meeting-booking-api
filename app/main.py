from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os


try:
    from router import router
    ROUTER_LOADED = True
    print("✅ Router loaded successfully!")
except Exception as e:
    print(f"❌ Could not load router: {e}")
    ROUTER_LOADED = False

app = FastAPI(
    title="Meeting Room Booking API",
    description="Simple Meeting Room Booking System with Docker + ngrok",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

if ROUTER_LOADED:
    app.include_router(router, prefix="/api/v1")
    print("✅ API routes registered successfully!")

@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "🏢 Welcome to Meeting Room Booking System",
        "version": "1.0.0",
        "status": "running",
        "router_loaded": ROUTER_LOADED,
        "api_base": "/api/v1" if ROUTER_LOADED else "Router not loaded"
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "router_loaded": ROUTER_LOADED
    }

if not ROUTER_LOADED:
    @app.get("/api/v1/status", tags=["Fallback"])
    def fallback_status():
        return {
            "message": "⚠️ Main router not loaded, using fallback endpoints",
            "issue": "Check router.py dependencies"
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)