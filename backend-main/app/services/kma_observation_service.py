# app/services/kma_observation_service.py

import os
import math
import requests
from datetime import datetime, timedelta

KMA_API_KEY = os.getenv("WEATHER_API_KEY")
ASOS_URL = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php"

# 자주 쓰는 ASOS 지점만 우선 등록
# 나중에 지상관측 지점정보 API로 자동화 가능
ASOS_STATIONS = [
    {"stn": "108", "name": "서울", "lat": 37.5714, "lon": 126.9658},
    {"stn": "112", "name": "인천", "lat": 37.4777, "lon": 126.6249},
    {"stn": "119", "name": "수원", "lat": 37.2575, "lon": 126.9830},
    # 경기권 보강
    {"stn": "99", "name": "파주", "lat": 37.88589, "lon": 126.76648},
    {"stn": "202", "name": "양평", "lat": 37.48863, "lon": 127.49446},
    {"stn": "203", "name": "이천", "lat": 37.26399, "lon": 127.48421},
    {"stn": "101", "name": "춘천", "lat": 37.9026, "lon": 127.7357},
    {"stn": "105", "name": "강릉", "lat": 37.7515, "lon": 128.8909},
    {"stn": "133", "name": "대전", "lat": 36.3720, "lon": 127.3721},
    {"stn": "131", "name": "청주", "lat": 36.6392, "lon": 127.4407},
    {"stn": "146", "name": "전주", "lat": 35.8215, "lon": 127.1549},
    {"stn": "156", "name": "광주", "lat": 35.1729, "lon": 126.8916},
    {"stn": "165", "name": "목포", "lat": 34.8173, "lon": 126.3815},
    {"stn": "143", "name": "대구", "lat": 35.8780, "lon": 128.6530},
    {"stn": "159", "name": "부산", "lat": 35.1047, "lon": 129.0320},
    {"stn": "152", "name": "울산", "lat": 35.5824, "lon": 129.3347},
    {"stn": "155", "name": "창원", "lat": 35.1702, "lon": 128.5728},
    {"stn": "184", "name": "제주", "lat": 33.5141, "lon": 126.5297},
]


ASOS_COLUMNS = [
    "TM", "STN", "WD", "WS", "GST_WD", "GST_WS", "GST_TM",
    "PA", "PS", "PT", "PR", "TA", "TD", "HM", "PV",
    "RN", "RN_DAY", "RN_INT", "SD_HR3", "SD_DAY", "SD_TOT",
    "WC", "WP", "WW", "CA_TOT", "CA_MID", "CH_MIN", "CT",
    "CT_TOP", "CT_MID", "CT_LOW", "VS", "SS", "SI",
    "ST_GD", "TS", "TE_005", "TE_01", "TE_02", "TE_03",
    "ST_SEA", "WH", "BF", "IR", "IX", "RN_JUN",
]


def _to_float(value):
    if value is None:
        return None

    value = str(value).strip()

    if value in ("", "-9", "-99", "-999", "-9999", "None", "null"):
        return None

    try:
        return float(value)
    except Exception:
        return None


def _distance_km(lat1, lon1, lat2, lon2):
    radius = 6371.0

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearest_asos_station(latitude, longitude):
    if latitude is None or longitude is None:
        # 좌표 없으면 서울 기본값
        return ASOS_STATIONS[0]

    try:
        lat = float(latitude)
        lon = float(longitude)
    except Exception:
        return ASOS_STATIONS[0]

    return min(
        ASOS_STATIONS,
        key=lambda s: _distance_km(lat, lon, s["lat"], s["lon"]),
    )


def _parse_asos_text(raw_text: str):
    rows = []

    for line in raw_text.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        parts = line.split()

        # 컬럼 수보다 짧으면 잘못된 줄
        if len(parts) < 12:
            continue

        row = {}

        for idx, col in enumerate(ASOS_COLUMNS):
            row[col] = parts[idx] if idx < len(parts) else None

        rows.append(row)

    return rows


def get_latest_asos_observation(latitude=None, longitude=None):
    """
    CCTV 좌표 기준 가장 가까운 ASOS 지점의 최근 관측값 조회.
    반환값:
    {
      temperature,
      precipitation,
      snowfall,
      visibility,
      raw
    }
    """
    if not KMA_API_KEY:
        print("[KMA] WEATHER_API_KEY 없음 → 관측값 저장 생략")
        return {}

    station = find_nearest_asos_station(latitude, longitude)

    # ASOS 시간자료라 최근 몇 시간 범위로 조회
    now = datetime.utcnow() + timedelta(hours=9)  # KST
    tm2 = now.strftime("%Y%m%d%H%M")
    tm1 = (now - timedelta(hours=6)).strftime("%Y%m%d%H%M")

    try:
        res = requests.get(
            ASOS_URL,
            params={
                "tm1": tm1,
                "tm2": tm2,
                "stn": station["stn"],
                "help": "0",
                "authKey": KMA_API_KEY,
            },
            timeout=20,
        )
        res.raise_for_status()

        rows = _parse_asos_text(res.text)

        if not rows:
            print(f"[KMA] ASOS 관측 데이터 없음 | station={station}")
            return {
                "station": station,
                "raw_text": res.text[:1000],
            }

        latest = rows[-1]

        temperature = _to_float(latest.get("TA"))
        precipitation = _to_float(latest.get("RN"))
        snowfall = _to_float(latest.get("SD_TOT"))

        # VS는 10m 단위 → m 단위로 저장
        vs = _to_float(latest.get("VS"))
        visibility = vs * 10 if vs is not None else None

        return {
            "temperature": temperature,
            "precipitation": precipitation,
            "snowfall": snowfall,
            "visibility": visibility,
            "station": station,
            "observed_at": latest.get("TM"),
            "raw": latest,
        }

    except Exception as e:
        print(f"[KMA] ASOS 관측값 조회 실패: {e}")
        return {
            "station": station,
            "error": str(e),
        }