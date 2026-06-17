import os
import time
import requests
from flask import current_app
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app import db
from app.models.cctv import CctvSource

_url_cache: dict = {}
CACHE_TTL = 60

CCTV_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Connection": "keep-alive",
}

def _make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session

def _save_to_db(items: list):
    try:
        for item in items:
            cctv_name = item.get("cctvname", "")
            if not cctv_name:
                continue
            existing = CctvSource.query.filter_by(cctv_name=cctv_name).first()
            if existing:
                existing.stream_url = item.get("cctvurl", "")
                existing.latitude = float(item.get("coordy", 0))
                existing.longitude = float(item.get("coordx", 0))
                existing.cctv_id = None  # API에 cctvid 없음
            else:
                db.session.add(CctvSource(
                    cctv_id=None,
                    cctv_name=cctv_name,
                    stream_url=item.get("cctvurl", ""),
                    latitude=float(item.get("coordy", 0)),
                    longitude=float(item.get("coordx", 0)),
                    provider="ITS",
                ))
        db.session.commit()
        current_app.logger.info(f"cctv_sources upsert 완료: {len(items)}건")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"cctv_sources upsert 실패: {e}")

def _load_from_db(limit: int) -> dict:
    try:
        rows = CctvSource.query.filter_by(active=True).limit(limit).all()
        if not rows:
            current_app.logger.warning("DB에도 CCTV 데이터 없음")
            return {"response": {"coordtype": 1, "datacount": 0, "data": []}}
        items = [
            {
                "cctvid": r.cctv_id,
                "cctvname": r.cctv_name,
                "cctvurl": r.stream_url or "",
                "coordx": str(r.longitude),
                "coordy": str(r.latitude),
                "roadsectionid": "",
            }
            for r in rows
        ]
        current_app.logger.info(f"DB 캐시에서 CCTV {len(items)}건 반환")
        return {"response": {"coordtype": 1, "datacount": len(items), "data": items}}
    except Exception as e:
        current_app.logger.error(f"DB 캐시 조회 실패: {e}")
        return {"response": {"coordtype": 1, "datacount": 0, "data": []}}

def get_fresh_stream_url(cctv_id: str, params: dict) -> str:
    now = time.time()
    if cctv_id in _url_cache:
        url, ts = _url_cache[cctv_id]
        if now - ts < CACHE_TTL:
            return url
    data = get_cctv_list(params, limit=100)
    for item in data.get("response", {}).get("data", []):
        _url_cache[item["cctvid"]] = (item["cctvurl"], now)
    return _url_cache.get(cctv_id, (None, None))[0]

def get_cctv_list(params: dict, limit: int = 20) -> dict:
    api_key = current_app.config.get("ITS_API_KEY") or os.getenv("ITS_API_KEY")
    base_url = "https://openapi.its.go.kr:9443/cctvInfo"

    if not api_key:
        raise ValueError("ITS_API_KEY가 없습니다.")

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

    try:
        response = requests.get(
            base_url,
            params=query_params,
            timeout=(3, 5),  # 연결 3초, 읽기 5초
            headers=CCTV_HEADERS,
            verify=False,
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("response", {}).get("data", [])

        if isinstance(items, list) and items:
            _save_to_db(items)
            data["response"]["data"] = items[:limit]
            return data

        current_app.logger.warning("ITS API datacount=0, DB 폴백")
        return _load_from_db(limit)

    except Exception as e:
        current_app.logger.warning(f"ITS API 실패, DB 폴백: {e}")
        return _load_from_db(limit)
        
def rewrite_m3u8(text: str, base_url: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append(line)
            continue
        if stripped.startswith("#"):
            lines.append(line)
            continue
        full_url = urljoin(base_url, stripped)
        proxy_url = f"/api/cctv-ts?url={requests.utils.quote(full_url, safe='')}"
        lines.append(proxy_url)
    return "\n".join(lines)

def fetch_stream_m3u8(stream_url: str) -> str:
    res = requests.get(stream_url, timeout=(3, 10), allow_redirects=True, headers=CCTV_HEADERS)
    res.raise_for_status()
    final_url = res.url
    base_url = final_url.rsplit('/', 1)[0] + '/'
    return rewrite_m3u8(res.text, base_url)

def fetch_segment(segment_url: str):
    res = requests.get(segment_url, stream=True, timeout=(3, 10), allow_redirects=True, headers=CCTV_HEADERS)
    res.raise_for_status()
    content_type = res.headers.get("content-type", "video/mp2t")
    is_m3u8 = (
        "mpegurl" in content_type.lower()
        or "m3u8" in content_type.lower()
        or segment_url.lower().endswith(".m3u8")
    )
    return content_type, is_m3u8, res

def rewrite_segment_m3u8(res, segment_url: str) -> str:
    final_url = res.url
    base_url = final_url.rsplit('/', 1)[0] + '/'
    return rewrite_m3u8(res.text, base_url)
