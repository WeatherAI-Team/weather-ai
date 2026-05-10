# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controller.ai_model_controller import router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "AI 서버 정상 작동 중!"}