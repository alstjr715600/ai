from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chatbot, community, districts, facilities

from app.database import engine, Base
from app import models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LocalHub MVP API",
    description="영유아와 함께 살기 좋은 서울 자치구 추천 MVP API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chatbot.router, prefix="/api/v1")
app.include_router(districts.router, prefix="/api/v1")
app.include_router(facilities.router, prefix="/api/v1")
app.include_router(community.router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["System"])
def health_check():
    return {"status": "UP"}
