import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.auth import router as auth_router
from api.v1.me import router as me_router

app = FastAPI(
    title="Toko API",
    version="1.0.0",
    description="API for Toko Bot Authentication & User Info"
)

# ✅ CORS config to allow frontend at localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add production URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API Routes
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(me_router, prefix="/api/v1", tags=["User Info"])

# ✅ Dev entrypoint
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
