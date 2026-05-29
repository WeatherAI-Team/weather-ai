# app/controller/ai_model_controller.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from app.service.ai_model_service import AIModelService
from pydantic import BaseModel
import cv2

router = APIRouter(prefix="/api/ai", tags=["AI"])
ai_model_service = AIModelService()
class ImagePathRequest(BaseModel):
    image_path: str

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
# 영상 분석 (저장 없이 결과만)
# ════════════════════════════════════════

@router.post("/analyze_video")
async def analyze_video(
    file: UploadFile = File(...),
    original_filename: str = Form("video.mp4")
):
    try:
        result = await ai_model_service.analyze_video_only(
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
        async def generate():
            async for chunk in ai_model_service.get_cctv_stream(rtsp_url):
                yield chunk

        return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")
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

# ════════════════════════════════════════
# Keras 1차 탐지 - 이미지 경로 기반
# backend-main에서 HTTP 요청으로 호출
# ═══════════════════════════════════════
@router.post("/detect/keras")
async def detect_keras_by_path(body: ImagePathRequest):
    try:
        frame = cv2.imread(body.image_path)

        if frame is None:
            raise HTTPException(
                status_code=400,
                detail="이미지를 읽을 수 없습니다."
            )

        result = ai_model_service._predict_weather(frame)

        return {
            "success": True,
            **result,
        }

    except HTTPException:
        raise

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }

# ════════════════════════════════════════
# YOLO 2차 정밀 탐지 - 이미지 경로 기반
# backend-main에서 HTTP 요청으로 호출
# ════════════════════════════════════════
@router.post("/detect/yolo")
async def detect_yolo_by_path(body: ImagePathRequest):
    try:
        frame = cv2.imread(body.image_path)

        if frame is None:
            raise HTTPException(
                status_code=400,
                detail="이미지를 읽을 수 없습니다."
            )

        keras_result = ai_model_service._predict_weather(frame)
        yolo_boxes = ai_model_service._run_yolo(frame, keras_result)

        return {
            "success": True,
            "keras_result": keras_result,
            "yolo_boxes": yolo_boxes,
            "yolo_detected": len(yolo_boxes) > 0,
        }

    except HTTPException:
        raise

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
    
