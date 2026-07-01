import os
import requests
from dotenv import load_dotenv
from app.services.ai_client_auth import AI_SERVER_HEADERS

load_dotenv()

AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")
AI_SERVER_TIMEOUT = int(os.getenv("AI_SERVER_TIMEOUT", "300"))

 
 
# ── 이미지 단건 탐지 ─────────────────────────────────────────────
def detect_image(file_storage) -> dict:
    """
    Flask FileStorage 객체를 받아 FastAPI AI 서버로 전송 후 결과 반환
    """
    files = {
        "file": (file_storage.filename, file_storage.read(), file_storage.content_type)
    }
    response = requests.post(
        f"{AI_SERVER_URL}/api/ai/detect",
        files=files,
        headers=AI_SERVER_HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
 
def analyze_video(file_storage, original_filename="video.mp4"):
    files = {
        "file": (
            file_storage.filename,
            file_storage.stream,
            file_storage.content_type,
        )
    }

    data = {
        "original_filename": original_filename,
    }

    response = requests.post(
        f"{AI_SERVER_URL}/api/ai/analyze_video",
        files=files,
        data=data,
        headers=AI_SERVER_HEADERS,
        timeout=AI_SERVER_TIMEOUT,
    )

    response.raise_for_status()
    return response.json()

# ── 영상 분석 및 저장 ────────────────────────────────────────────
def analyze_and_save_video(file_storage, user_id: str, original_filename: str) -> dict:
    """
    영상 파일을 FastAPI AI 서버로 전송하여 분석 및 저장 후 결과 반환
    """
    files = {
        "file": (file_storage.filename, file_storage.read(), file_storage.content_type)
    }
    data = {
        "user_id": user_id,
        "original_filename": original_filename,
    }
    response = requests.post(
        f"{AI_SERVER_URL}/api/ai/analyze_and_save_video",
        files=files,
        data=data,
        headers=AI_SERVER_HEADERS,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()