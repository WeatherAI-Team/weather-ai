import os
from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context
from ..services.cctv_service import get_cctv_list
import requests

AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://localhost:8000")

cctv_bp = Blueprint("cctv", __name__)

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
        current_app.logger.error(f"CCTV API 오류: {e}")
        return jsonify({"error": str(e)}), 500

@cctv_bp.route("/cctv/stream")
def stream_proxy():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "url 파라미터 없음"}), 400

    req = requests.get(url, timeout=10, allow_redirects=True)
    final_url = req.url
    base_url = final_url.rsplit('/', 1)[0] + '/'

    print(f"최종 URL: {final_url}")
    print(f"base_url: {base_url}")
    print(f"m3u8 내용: {req.text[:300]}")

    lines = []
    for line in req.text.splitlines():
        if line and not line.startswith('#'):
            if not line.startswith('http'):
                full_url = base_url + line
            else:
                full_url = line
            line = f"/api/cctv-ts?url={requests.utils.quote(full_url)}"
        lines.append(line)

    return Response('\n'.join(lines), content_type="application/vnd.apple.mpegurl")

@cctv_bp.route("/cctv/<path:segment_path>", methods=["GET"])
def segment_proxy(segment_path):
    query_string = request.query_string.decode()
    segment_url = f"http://cctvsec.ktict.co.kr/{segment_path}"
    if query_string:
        segment_url += f"?{query_string}"
    try:
        res = requests.get(segment_url, timeout=10, allow_redirects=True)
        content_type = res.headers.get("content-type", "video/mp2t")

        if "mpegurl" in content_type or segment_path.endswith(".m3u8"):
            final_url = res.url
            base_url = final_url.rsplit('/', 1)[0] + '/'
            print(f"세그먼트 playlist 최종 URL: {final_url}")
            print(f"내용: {res.text[:300]}")
            lines = []
            for line in res.text.splitlines():
                if line and not line.startswith('#'):
                    if not line.startswith('http'):
                        full_url = base_url + line
                    else:
                        full_url = line
                    line = f"/api/cctv-ts?url={requests.utils.quote(full_url)}"
                lines.append(line)
            return Response('\n'.join(lines), content_type="application/vnd.apple.mpegurl")

        return Response(
            stream_with_context(res.iter_content(chunk_size=4096)),
            content_type=content_type
        )
    except Exception as e:
        current_app.logger.error(f"세그먼트 프록시 실패: {e}")
        return jsonify({"error": str(e)}), 500

@cctv_bp.route("/ai/detect", methods=["POST"])
def detect_image():
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없습니다."}), 400
    file = request.files['file']
    try:
        files = {"file": (file.filename, file.read(), file.content_type)}
        response = requests.post(f"{AI_SERVER_URL}/api/ai/detect", files=files, timeout=60)
        return jsonify(response.json()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cctv_bp.route("/ai/analyze_and_save_video", methods=["POST"])
def analyze_video():
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없습니다."}), 400
    file = request.files['file']
    user_id = request.form.get('user_id', '1')
    original_filename = request.form.get('original_filename', file.filename)
    try:
        files = {"file": (file.filename, file.read(), file.content_type)}
        data = {"user_id": user_id, "original_filename": original_filename}
        response = requests.post(f"{AI_SERVER_URL}/api/ai/analyze_and_save_video", files=files, data=data, timeout=60)
        return jsonify(response.json()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cctv_bp.route("/cctv-ts", methods=["GET"])
def ts_proxy():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "url 없음"}), 400
    try:
        res = requests.get(url, stream=True, timeout=10, allow_redirects=True)
        content_type = res.headers.get("content-type", "video/mp2t")

        if "mpegurl" in content_type or url.endswith(".m3u8"):
            final_url = res.url
            base_url = final_url.rsplit('/', 1)[0] + '/'
            lines = []
            for line in res.text.splitlines():
                if line and not line.startswith('#'):
                    if not line.startswith('http'):
                        full_url = base_url + line
                    else:
                        full_url = line
                    line = f"/api/cctv-ts?url={requests.utils.quote(full_url)}"
                lines.append(line)
            return Response('\n'.join(lines), content_type="application/vnd.apple.mpegurl")

        return Response(
            stream_with_context(res.iter_content(chunk_size=4096)),
            content_type="video/mp2t"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500