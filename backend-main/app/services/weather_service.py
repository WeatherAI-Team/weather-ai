import os
import requests
from dotenv import load_dotenv

load_dotenv()

KMA_API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "https://apihub.kma.go.kr/api/typ01/url/wrn_met_data.php"

# 악천후 특보 코드
DANGEROUS_WRN = {
    "R": "호우",
    "S": "대설",
    "F": "안개",
    "W": "강풍",
    "T": "태풍",
}

def get_weather_alerts():
    if not KMA_API_KEY:
        raise RuntimeError("WEATHER_API_KEY가 설정되지 않았습니다.")

    params = {
        "reg": "0",
        "wrn": "A",
        "tmfc1": "",
        "tmfc2": "",
        "disp": "0",
        "help": "1",
        "authKey": KMA_API_KEY,
    }
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.text

def parse_alerts(raw_text: str) -> list:
    alerts = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 7:
            continue
        wrn_code = parts[5]
        lvl = parts[6]
        if wrn_code in DANGEROUS_WRN and lvl in ["2", "3"]:
            alerts.append({
                "wrn_code": wrn_code,
                "wrn_name": DANGEROUS_WRN[wrn_code],
                "level": "경보" if lvl == "3" else "주의보",
                "reg_id": parts[4],
                "tm_fc": parts[0],
            })
    return alerts

def is_dangerous() -> tuple:
    raw = get_weather_alerts()
    alerts = parse_alerts(raw)
    return len(alerts) > 0, alerts

def build_weather_summary(alert: dict) -> str:
    """
    Gemma에 원문 전체를 보내지 않고,
    필요한 정보만 짧게 요약해서 토큰 사용량을 줄인다.
    """
    return (
        f"{alert['wrn_name']} {alert['level']} 발령 "
        f"(구역: {alert['reg_id']}, 발표시각: {alert['tm_fc']})"
    )