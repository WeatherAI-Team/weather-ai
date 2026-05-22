# app/controller/ai_model_controller.py
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from app.service.ai_model_service import AIModelService

router = APIRouter(prefix="/api/ai", tags=["AI"])
ai_model_service = AIModelService()


# ════════════════════════════════════════
# 이미지/영상 분석 (저장 없이 결과만)
# ════════════════════════════════════════

@router.post("/detect")
async def detect(file: UploadFile = File(...)):
    try:
        result = await ai_model_service.detect_image(file)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ════════════════════════════════════════
# 이미지 분석 + 저장
# ════════════════════════════════════════

@router.post("/detect_and_save")
async def detect_and_save(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    original_filename: str = Form("image.jpg")
):
    try:
        result = await ai_model_service.detect_and_save_image(
            user_id=user_id,
            file=file,
            original_filename=original_filename,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ════════════════════════════════════════
# 영상 분석 + 저장
# ════════════════════════════════════════

@router.post("/analyze_and_save_video")
async def analyze_and_save_video(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    original_filename: str = Form("video.mp4")
):
    try:
        result = await ai_model_service.analyze_and_save_video(
            user_id=user_id,
            file=file,
            original_filename=original_filename,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ════════════════════════════════════════
# CCTV 실시간 스트리밍
# ════════════════════════════════════════

@router.post("/cctv_stream")
async def cctv_stream(body: dict):
    rtsp_url = body.get("url")
    if not rtsp_url:
        return {"success": False, "message": "URL이 없습니다."}
    try:
        stream = ai_model_service.get_cctv_stream(rtsp_url)
        return StreamingResponse(stream, media_type="multipart/x-mixed-replace; boundary=frame")
    except Exception as e:
        return {"success": False, "error": str(e)}


# ════════════════════════════════════════
# 분석 중지
# ════════════════════════════════════════

@router.post("/stop")
async def stop_analysis():
    try:
        ai_model_service.stop_analysis()
        return {"success": True, "message": "분석 중지됨"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ════════════════════════════════════════
# 분석 상태 확인
# ════════════════════════════════════════

@router.get("/status")
async def get_status():
    return {
        "is_analyzing": ai_model_service.is_analyzing,
        "stop_requested": ai_model_service.stop_requested
    }