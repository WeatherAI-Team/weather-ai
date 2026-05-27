import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN"),
)


def _call_gemma(messages, max_tokens=500, temperature=0.2) -> str:
    completion = client.chat.completions.create(
        model=os.getenv("GEMMA_MODEL", "google/gemma-3n-E4B-it"),
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    print("Gemma 응답:", completion.choices[0].message.content)

    content = completion.choices[0].message.content

    if not content:
        raise RuntimeError(
            "Gemma 응답 content가 비어 있습니다. max_tokens를 늘리거나 프롬프트를 더 짧게 조정하세요."
        )

    return content.strip()


def _safe_json_loads(text: str) -> dict:
    """
    Gemma가 JSON 앞뒤에 설명을 붙일 수도 있어서
    최대한 JSON 부분만 뽑아서 dict로 변환.
    """
    try:
        return json.loads(text)
    except Exception:
        pass

    try:
        start = text.find("{")
        end = text.rfind("}") + 1

        if start != -1 and end != -1:
            return json.loads(text[start:end])
    except Exception:
        pass

    return {
        "raw_message": text
    }

def _normalize_final_alert_result(result: dict) -> dict:
    """
    Gemma가 {"alerts": [{...}]} 형태로 감싸서 응답해도
    서비스와 DB 저장에서 쓰는 단일 dict 형태로 보정한다.
    """

    if not isinstance(result, dict):
        result = {}

    if (
        isinstance(result.get("alerts"), list)
        and len(result["alerts"]) > 0
        and isinstance(result["alerts"][0], dict)
    ):
        result = result["alerts"][0]

    result.setdefault("risk_level", "CAUTION")
    result.setdefault("title", "위험 차량 감지 알림")
    result.setdefault("admin_message", "관제센터 확인 필요")
    result.setdefault("driver_message", "감속하고 안전거리를 확보하세요.")
    result.setdefault("reason", "기상 및 차량 탐지 결과 기반 알림")
    result.setdefault("alert_required", True)
    result.setdefault("false_positive_suspected", False)

    return result

def generate_alert_message(weather_data: str) -> str:
    """
    기존 함수.
    운전자용 짧은 알림이나 단순 테스트용으로 사용.
    지금 콘솔 테스트 성공한 함수라 일단 유지.
    """
    messages = [
        {
            "role": "user",
            "content": (
                "You are a weather expert. "
                "Analyze this Korean weather alert data and generate "
                "a short Korean warning message under 50 characters:\n"
                f"{weather_data}"
            )
        }
    ]

    return _call_gemma(messages, max_tokens=300, temperature=0.2)


def judge_weather_gate(weather_data: str) -> dict:
    """
    1단계: LLM Gate.
    기상청 API 데이터를 보고 CCTV 감시 시스템을 활성화할지 판단.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI gate for a severe-weather traffic control system. "
                "Your job is to decide whether the CCTV monitoring and vehicle detection system "
                "should be activated based on Korean weather alert data. "
                "Return ONLY valid JSON. Do not use markdown. "
                "The JSON must have these keys: "
                "monitoring_required(boolean), risk_level(string), reason(string). "
                "risk_level must be one of LOW, NORMAL, CAUTION, DANGER. "
                "The reason must be written in Korean."
            ),
        },
        {
            "role": "user",
            "content": f"Korean weather alert data:\n{weather_data}",
        },
    ]

    result_text = _call_gemma(messages, max_tokens=700, temperature=0.1)
    return _safe_json_loads(result_text)


def generate_final_alert(weather_data: dict, detection_result: dict) -> dict:
    """
    최종 단계:
    기상청 데이터 + 차량 탐지 결과를 바탕으로
    관리자용 알림 + 운전자용 알림 생성.
    """
    input_data = {
        "weather_data": weather_data,
        "detection_result": detection_result,
    }

    messages = [
        {
            "role": "system",
            "content": (
                "Return only valid JSON. "
                "The first character must be { and the last character must be }. "
                "Do not use markdown. "
                "Do not explain. "
                "Return exactly one JSON object. Do not wrap the response in an alerts array. "
                "Create Korean alerts for a severe-weather hazardous vehicle monitoring system. "
                "JSON keys: risk_level, title, admin_message, driver_message, reason, alert_required, false_positive_suspected. "
                "risk_level must be LOW, NORMAL, CAUTION, or DANGER. "
                "admin_message is for control center operators. "
                "driver_message is a short warning for drivers. "
                "All values except risk_level must be Korean. "
                "title is a short Korean event title. "
                "alert_required must be boolean. "
                "false_positive_suspected must be boolean. "
                "driver_message must include a concrete driving action such as 감속, 안전거리 확보, 차선 변경 자제. "
            ),
        },
        {
            "role": "user",
            "content": json.dumps(input_data, ensure_ascii=False),
        },
    ]

    result_text = _call_gemma(messages, max_tokens=1000, temperature=0.1)
    result = _safe_json_loads(result_text)

    return _normalize_final_alert_result(result)

