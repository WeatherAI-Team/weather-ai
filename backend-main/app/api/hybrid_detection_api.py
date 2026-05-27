# backend-main/app/api/hybrid_detection_api.py

from flask import Blueprint, request, jsonify, current_app
from app.services.hybrid_alert_service import run_hybrid_detection_flow

hybrid_detection_bp = Blueprint(
    "hybrid_detection",
    __name__,
    url_prefix="/api/detections"
)


@hybrid_detection_bp.route("/analyze", methods=["POST"])
def analyze_detection():
    try:
        data = request.get_json() or {}
        if not data.get("image_path"):
            return jsonify({
                "success": False,
                "message": "image_path가 필요합니다.",
            }), 400

        result = run_hybrid_detection_flow(
            image_path=data.get("image_path"),
            cctv_source_id=data.get("cctv_source_id"),
            weather_log_id=data.get("weather_log_id"),
        )

        return jsonify({
            "success": True,
            "data": result,
        }), 200

    except Exception:
        current_app.logger.exception("하이브리드 탐지 처리 중 오류 발생")
        return jsonify({
            "success": False,
            "message": "탐지 처리 중 오류가 발생했습니다.",
        }), 500