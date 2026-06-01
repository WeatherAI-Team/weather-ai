from flask import Blueprint, request, jsonify, Response, stream_with_context, current_app

from ..services.cctv_service import (
    get_cctv_list,
    fetch_stream_m3u8,
    fetch_segment,
    rewrite_segment_m3u8,
)
from ..services.ai_service import (
    detect_image,
    analyze_and_save_video,
    analyze_video as request_analyze_video,
)

from app.services.cctv_gate_service import get_cctv_monitoring_gate
import os
from jose import jwt, JWTError
cctv_bp = Blueprint("cctv", __name__)

def _get_token_payload():
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None, (
            jsonify({
                "success": False,
                "message": "인증 토큰이 없습니다.",
            }),
            401,
        )

    token = auth_header.split(" ", 1)[1]

    secret_key = os.getenv("SECRET_KEY") or current_app.config.get("SECRET_KEY")

    algorithm = (
        current_app.config.get("JWT_ALGORITHM")
        or os.getenv("JWT_ALGORITHM")
        or "HS256"
    )

    if not secret_key:
        return None, (
            jsonify({
                "success": False,
                "message": "JWT_SECRET_KEY가 설정되지 않았습니다.",
            }),
            500,
        )

    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
        )
        return payload, None

    except JWTError:
        return None, (
            jsonify({
                "success": False,
                "message": "유효하지 않은 토큰입니다.",
            }),
            401,
        )


def _require_admin():
    payload, error_response = _get_token_payload()

    if error_response:
        return None, error_response

    role = payload.get("role")

    if role != "admin":
        return None, (
            jsonify({
                "success": False,
                "message": "관리자만 CCTV Gate 상태를 조회할 수 있습니다.",
            }),
            403,
        )

    return payload, None


# ── CCTV 목록 조회 ───────────────────────────────────────────────
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
    limit = int(request.args.get("limit", 20))
    try:
        data = get_cctv_list(params, limit)
        return jsonify(data), 200
    except Exception as e:
        current_app.logger.error(f"CCTV 목록 조회 실패: {e}")
        return jsonify({"error": str(e)}), 500


# ── HLS 스트림 m3u8 프록시 ───────────────────────────────────────
@cctv_bp.route("/cctv/stream")
def stream_proxy():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "url 파라미터 없음"}), 400
    try:
        rewritten = fetch_stream_m3u8(url)
        return Response(rewritten, content_type="application/vnd.apple.mpegurl")
    except Exception as e:
        current_app.logger.error(f"스트림 프록시 실패: {e}")
        return jsonify({"error": str(e)}), 504


# ── TS 세그먼트 프록시 ───────────────────────────────────────────
@cctv_bp.route("/cctv-ts", methods=["GET"])
def ts_proxy():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "url 없음"}), 400
    try:
        content_type, is_m3u8, res = fetch_segment(url)

        if is_m3u8:
            rewritten = rewrite_segment_m3u8(res, url)
            return Response(rewritten, content_type="application/vnd.apple.mpegurl")

        return Response(
            stream_with_context(res.iter_content(chunk_size=4096)),
            content_type="video/mp2t",
        )
    except Exception as e:
        current_app.logger.error(f"TS 프록시 실패: {e}")
        return jsonify({"error": str(e)}), 500


# ── 이미지 단건 탐지 ─────────────────────────────────────────────
@cctv_bp.route("/ai/detect", methods=["POST"])
def detect():
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없습니다."}), 400
    try:
        result = detect_image(request.files['file'])
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"이미지 탐지 실패: {e}")
        return jsonify({"error": str(e)}), 500


# ── 영상 분석 및 저장 ────────────────────────────────────────────
@cctv_bp.route("/ai/analyze_and_save_video", methods=["POST"])
def analyze_video():
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없습니다."}), 400
    try:
        result = analyze_and_save_video(
            file_storage=request.files['file'],
            user_id=request.form.get('user_id', '1'),
            original_filename=request.form.get('original_filename', request.files['file'].filename),
        )
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"영상 분석 실패: {e}")
        return jsonify({"error": str(e)}), 500


# ── 세그먼트 경로 프록시 (레거시 호환) ──────────────────────────
@cctv_bp.route("/cctv/<path:segment_path>", methods=["GET"])
def segment_proxy(segment_path):
    query_string = request.query_string.decode()
    segment_url = f"http://cctvsec.ktict.co.kr/{segment_path}"
    if query_string:
        segment_url += f"?{query_string}"
    try:
        content_type, is_m3u8, res = fetch_segment(segment_url)

        if is_m3u8:
            rewritten = rewrite_segment_m3u8(res, segment_url)
            return Response(rewritten, content_type="application/vnd.apple.mpegurl")

        return Response(
            stream_with_context(res.iter_content(chunk_size=4096)),
            content_type=content_type,
        )
    except Exception as e:
        current_app.logger.error(f"세그먼트 프록시 실패: {e}")
        return jsonify({"error": str(e)}), 500
    
# ── 영상 분석 (저장 없이 결과만) ─────────────────────────────────
@cctv_bp.route("/ai/analyze_video", methods=["POST"])
def analyze_video_only():
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없습니다."}), 400

    try:
        result = request_analyze_video(
            request.files['file'],
            original_filename=request.form.get(
                'original_filename',
                request.files['file'].filename
            ),
        )

        return jsonify(result), 200

    except Exception as e:
        current_app.logger.error(f"영상 분석 실패: {e}")
        return jsonify({"error": str(e)}), 500
    
# ── CCTV Gemma Gate 상태 조회 관리자 전용 ─────────────────────────
@cctv_bp.route("/cctv/gate", methods=["GET"])
def cctv_gate():
    _payload, error_response = _require_admin()

    if error_response:
        return error_response

    try:
        result = get_cctv_monitoring_gate()

        return jsonify({
            "success": True,
            "data": result,
        }), 200

    except Exception as e:
        current_app.logger.exception("CCTV Gate 판단 실패")

        return jsonify({
            "success": False,
            "message": "CCTV Gate 판단 중 오류가 발생했습니다.",
            "error": str(e),
        }), 500