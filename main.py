from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, users, events, admin
from app.config import settings
from app.utils.pincode_initializer import initialize_pincodes, check_storage_connection_and_ensure_bucket
from contextlib import asynccontextmanager

# Create database tables
Base.metadata.create_all(bind=engine)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    # initialize pincodes CSV -> DB
    initialize_pincodes()
    # ensure storage connectivity and bucket exists (reads GCS_BUCKET_NAME and STORAGE_EMULATOR_HOST from env)
    try:
        check_storage_connection_and_ensure_bucket()
    except Exception as e:
        # If storage check fails, raise so the app doesn't start silently broken
        raise
    yield
    # Shutdown code (if needed)
    # cleanup_resources()
    
app = FastAPI(
    title="CYO Backend API",
    description="Production-ready authentication API with JWT",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan
)

# List of allowed origins
origins = [
    "http://localhost:8080",
    "http://localhost:8081",
    # Add your Vercel frontend URL here once it's deployed
    # Example: "https://your-project-name.vercel.app"
]

# CORS middleware - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"message": "Welcome to CYO Backend API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
