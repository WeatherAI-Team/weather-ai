import requests
from flask import current_app

# app/services/cctv_service.py
def get_cctv_list(params: dict, limit: int = 20) -> dict:
    api_key = current_app.config.get("ITS_API_KEY") or __import__('os').getenv("ITS_API_KEY")
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

    # 갯수 제한 — 응답 구조에 맞게 슬라이싱
    items = data.get("response", {}).get("data", [])
    if isinstance(items, list):
        data["response"]["data"] = items[:limit]

    return data