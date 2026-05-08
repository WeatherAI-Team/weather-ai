from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context
from ..services.cctv_service import get_cctv_list

import requests


cctv_bp = Blueprint("cctv", __name__)

# app/api/cctv_api.py
@cctv_bp.route("/cctv", methods=["GET"])
def cctv_list():
    params = {
        "type":     request.args.get("type",     "its"),
        "cctvType": request.args.get("cctvType", "1"),
        "minX":     request.args.get("minX",     "126.5"),
        "maxX":     request.args.get("maxX",     "127.5"),
        "minY":     request.args.get("minY",     "37.0"),
        "maxY":     request.args.get("maxY",     "38.0"),
        "getType":  request.args.get("getType",  "json"),
    }
    limit = int(request.args.get("limit", 20))  # 기본 20개

    try:
        data = get_cctv_list(params, limit)
        return jsonify(data), 200
    except Exception as e:
        current_app.logger.error(f"CCTV API 오류: {e}")
        return jsonify({"error": str(e)}), 500
    
@cctv_bp.route("/cctv/stream")
def stream_proxy():
    """
    브라우저 → Flask → CCTV 서버
    CORS 우회용 프록시
    """
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "url 파라미터 없음"}), 400

    req = requests.get(url, stream=True, timeout=10)
    
    return Response(
        stream_with_context(req.iter_content(chunk_size=1024)),
        content_type=req.headers.get("Content-Type", "video/mp2t"),
    )