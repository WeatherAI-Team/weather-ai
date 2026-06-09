from flask import Blueprint, request, jsonify, Response, stream_with_context, current_app
import requests 
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
    # 프론트가 보낸 원본 m3u8 주소를 가져와.
    url = request.args.get("url")

    # 주소가 없으면 잘못된 요청이야.
    if not url:
        return jsonify({
            "success": False,
            "message": "url 파라미터 없음"
        }), 400

    try:
        # 원본 m3u8을 가져와서 내부 세그먼트 주소를 프록시 주소로 바꿔.
        rewritten = fetch_stream_m3u8(url)

        return Response(
            rewritten,
            content_type="application/vnd.apple.mpegurl",
            headers={
                "Cache-Control": "no-store"
            }
        )

    except requests.exceptions.Timeout as e:
        # 원본 m3u8 서버가 너무 늦게 응답한 경우야.
        current_app.logger.warning(f"스트림 프록시 타임아웃: {e}")
        current_app.logger.warning(f"스트림 프록시 타임아웃 URL: {url}")

        return jsonify({
            "success": False,
            "message": "CCTV 스트림 응답 시간이 초과되었습니다."
        }), 504

    except requests.exceptions.RequestException as e:
        # 원본 m3u8 요청이 실패한 경우야.
        current_app.logger.warning(f"스트림 프록시 원본 요청 실패: {e}")
        current_app.logger.warning(f"스트림 프록시 실패 URL: {url}")

        return jsonify({
            "success": False,
            "message": "CCTV 스트림을 가져오지 못했습니다."
        }), 502

    except Exception as e:
        # 진짜 백엔드 내부 오류야.
        current_app.logger.error(f"스트림 프록시 서버 내부 오류: {e}")
        current_app.logger.error(f"스트림 프록시 서버 내부 오류 URL: {url}")

        return jsonify({
            "success": False,
            "message": "CCTV 스트림 처리 중 서버 오류가 발생했습니다."
        }), 500

# ── TS 세그먼트 프록시 ───────────────────────────────────────────
# ── TS 세그먼트 프록시 ───────────────────────────────────────────
@cctv_bp.route("/cctv-ts", methods=["GET"])
def ts_proxy():
    # 프론트가 보낸 CCTV 영상 조각 주소를 가져와.
    url = request.args.get("url")

    # 주소가 없으면 요청이 잘못된 거야.
    if not url:
        return jsonify({
            "success": False,
            "message": "url 없음"
        }), 400

    try:
        # CCTV 원본 서버에서 영상 조각 또는 m3u8 파일을 가져와.
        content_type, is_m3u8, res = fetch_segment(url)

        # 가져온 게 m3u8이면 안에 있는 영상 조각 주소를 다시 프록시 주소로 바꿔줘.
        if is_m3u8:
            rewritten = rewrite_segment_m3u8(res, url)

            return Response(
                rewritten,
                content_type="application/vnd.apple.mpegurl",
                headers={
                    "Cache-Control": "no-store"
                }
            )

        # 가져온 게 ts 영상 조각이면 프론트로 그대로 보내줘.
        return Response(
            stream_with_context(res.iter_content(chunk_size=4096)),
            content_type=content_type or "video/mp2t",
            headers={
                "Cache-Control": "no-store"
            }
        )

    except requests.exceptions.Timeout as e:
        # CCTV 원본 서버가 너무 늦게 응답한 경우야.
        current_app.logger.warning(f"TS 프록시 타임아웃: {e}")
        current_app.logger.warning(f"TS 프록시 타임아웃 URL: {url}")

        return jsonify({
            "success": False,
            "message": "CCTV 원본 서버 응답 시간이 초과되었습니다."
        }), 504

    except requests.exceptions.RequestException as e:
        # CCTV 원본 서버 연결 실패, 403, 404, 500 등이 여기로 들어와.
        current_app.logger.warning(f"TS 프록시 원본 요청 실패: {e}")
        current_app.logger.warning(f"TS 프록시 실패 URL: {url}")

        return jsonify({
            "success": False,
            "message": "CCTV 원본 영상을 가져오지 못했습니다."
        }), 502

    except Exception as e:
        # 진짜 우리 백엔드 코드에서 예상 못 한 오류가 난 경우야.
        current_app.logger.error(f"TS 프록시 서버 내부 오류: {e}")
        current_app.logger.error(f"TS 프록시 서버 내부 오류 URL: {url}")

        return jsonify({
            "success": False,
            "message": "CCTV 프록시 처리 중 서버 오류가 발생했습니다."
        }), 500


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
    
