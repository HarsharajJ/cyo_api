from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth, users, events
from app.config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CYO Backend API",
    description="Production-ready authentication API with JWT",
    version="1.0.0",
    debug=settings.debug
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)

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
