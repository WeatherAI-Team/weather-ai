import os
import requests
from flask import current_app


# ── ITS CCTV 목록 조회 ──────────────────────────────────────────
def get_cctv_list(params: dict, limit: int = 20) -> dict:
    api_key = current_app.config.get("ITS_API_KEY") or os.getenv("ITS_API_KEY")
    base_url = "https://openapi.its.go.kr:9443/cctvInfo"

    if not api_key:
        raise ValueError("ITS_API_KEY가 없습니다. .env 확인하세요.")

    query_params = {
        "apiKey":   api_key,
        "type":     params["type"],
        "cctvType": params["cctvType"],
        "minX":     params["minX"],
        "maxX":     params["maxX"],
        "minY":     params["minY"],
        "maxY":     params["maxY"],
        "getType":  params.get("getType", "json"),
    }

    response = requests.get(base_url, params=query_params, timeout=10)
    response.raise_for_status()
    data = response.json()

    items = data.get("response", {}).get("data", [])
    if isinstance(items, list):
        data["response"]["data"] = items[:limit]

    return data


# ── m3u8 파싱 및 URL 재작성 (공통 유틸) ──────────────────────────
def rewrite_m3u8(text: str, base_url: str) -> str:
    """
    m3u8 내 상대경로 세그먼트를 /api/cctv-ts?url=... 형태로 재작성
    """
    lines = []
    for line in text.splitlines():
        if line and not line.startswith('#'):
            if not line.startswith('http'):
                full_url = base_url + line
            else:
                full_url = line
            line = f"/api/cctv-ts?url={requests.utils.quote(full_url)}"
        lines.append(line)
    return '\n'.join(lines)


# ── HLS 스트림 m3u8 가져오기 ─────────────────────────────────────
def fetch_stream_m3u8(stream_url: str) -> str:
    """
    원본 m3u8을 가져와서 세그먼트 URL을 프록시 경로로 재작성한 텍스트 반환
    """
    res = requests.get(stream_url, timeout=5, allow_redirects=True)
    res.raise_for_status()

    final_url = res.url
    base_url = final_url.rsplit('/', 1)[0] + '/'

    current_app.logger.debug(f"[stream] 최종 URL: {final_url}")
    current_app.logger.debug(f"[stream] m3u8 앞부분: {res.text[:300]}")

    return rewrite_m3u8(res.text, base_url)


# ── TS 세그먼트 / 중간 playlist 가져오기 ─────────────────────────
def fetch_segment(segment_url: str):
    """
    세그먼트(ts) 또는 중간 playlist(m3u8) 응답을 반환
    반환값: (content_type, is_m3u8, response_object)
    """
    res = requests.get(segment_url, stream=True, timeout=5, allow_redirects=True)
    res.raise_for_status()

    content_type = res.headers.get("content-type", "video/mp2t")
    is_m3u8 = "mpegurl" in content_type or segment_url.endswith(".m3u8")

    return content_type, is_m3u8, res


# ── TS URL로 m3u8 재작성 (중간 playlist 대응) ────────────────────
def rewrite_segment_m3u8(res, segment_url: str) -> str:
    """
    중간 playlist일 때 세그먼트 URL을 프록시 경로로 재작성
    """
    final_url = res.url
    base_url = final_url.rsplit('/', 1)[0] + '/'

    current_app.logger.debug(f"[segment] playlist 최종 URL: {final_url}")
    current_app.logger.debug(f"[segment] 내용: {res.text[:300]}")

    return rewrite_m3u8(res.text, base_url)