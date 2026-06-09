import os
import requests
from flask import current_app
from urllib.parse import urljoin

import time

# URL 캐시: {cctv_id: (url, timestamp)}
_url_cache: dict = {}
CACHE_TTL = 60  # 60초마다 URL 재발급

def get_fresh_stream_url(cctv_id: str, params: dict) -> str:
    now = time.time()
    if cctv_id in _url_cache:
        url, ts = _url_cache[cctv_id]
        if now - ts < CACHE_TTL:
            return url  # 아직 유효
    
    # 새로 발급
    data = get_cctv_list(params, limit=100)
    for item in data.get("response", {}).get("data", []):
        _url_cache[item["cctvid"]] = (item["cctvurl"], now)
    
    return _url_cache.get(cctv_id, (None, None))[0]

# CCTV 원본 서버에 요청할 때 공통으로 사용할 헤더야.
# 일부 CCTV 서버는 User-Agent가 없으면 요청을 막거나 불안정하게 응답할 수 있어.
CCTV_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Connection": "keep-alive",
}

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

    response = requests.get(base_url, params=query_params, timeout=(5, 15), headers= CCTV_HEADERS,)
    response.raise_for_status()
    data = response.json()

    items = data.get("response", {}).get("data", [])
    if isinstance(items, list):
        data["response"]["data"] = items[:limit]

    return data


# ── m3u8 파싱 및 URL 재작성 (공통 유틸) ──────────────────────────
def rewrite_m3u8(text: str, base_url: str) -> str:
    """
    원본 m3u8 안에 있는 ts 세그먼트 주소를
    우리 백엔드 프록시 주소인 /api/cctv-ts?url=... 형태로 바꿔주는 함수야.
    """

    # 새로 만들어줄 m3u8 줄들을 담는 리스트야.
    lines = []

    # m3u8 내용을 한 줄씩 읽어.
    for line in text.splitlines():
        # 양쪽 빈칸을 제거한 줄이야.
        stripped = line.strip()

        # 빈 줄이면 그대로 추가해.
        if not stripped:
            lines.append(line)
            continue

        # #으로 시작하는 줄은 설정 정보라서 주소가 아니야.
        # 예: #EXTM3U, #EXTINF 같은 줄
        if stripped.startswith("#"):
            lines.append(line)
            continue

        # 여기까지 왔으면 영상 조각 주소일 가능성이 커.
        # urljoin은 상대경로와 절대경로를 안전하게 합쳐줘.
        # 예: base_url + "../abc.ts" 같은 것도 안전하게 처리해.
        full_url = urljoin(base_url, stripped)

        # 원본 영상 조각 주소를 우리 백엔드 프록시 주소로 바꿔.
        # safe=''는 URL 안의 ?, &, / 같은 문자가 꼬이지 않게 전부 인코딩해주는 옵션이야.
        proxy_url = f"/api/cctv-ts?url={requests.utils.quote(full_url, safe='')}"

        # 바꾼 주소를 m3u8 줄 목록에 추가해.
        lines.append(proxy_url)

    # 줄들을 다시 m3u8 텍스트로 합쳐서 돌려줘.
    return "\n".join(lines)


# ── HLS 스트림 m3u8 가져오기 ─────────────────────────────────────
def fetch_stream_m3u8(stream_url: str) -> str:
    """
    원본 m3u8을 가져와서 세그먼트 URL을 프록시 경로로 재작성한 텍스트 반환
    """
    res = requests.get(stream_url, timeout=(3,10), allow_redirects=True, headers=CCTV_HEADERS,)
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
    res = requests.get(segment_url, stream=True, timeout=(3,10), allow_redirects=True, headers=CCTV_HEADERS,)
    res.raise_for_status()

    content_type = res.headers.get("content-type", "video/mp2t")
    is_m3u8 = (
        "mpegurl" in content_type.lower()
        or "m3u8" in content_type.lower()
        or segment_url.lower().endswith(".m3u8")
    )

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