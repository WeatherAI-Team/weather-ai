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
        model="google/gemma-4-31B-it:together",
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
                "Create Korean alerts for a severe-weather hazardous vehicle monitoring system. "
                "JSON keys: risk_level, admin_message, driver_message, reason. "
                "risk_level must be LOW, NORMAL, CAUTION, or DANGER. "
                "admin_message is for control center operators. "
                "driver_message is a short warning for drivers. "
                "All values except risk_level must be Korean."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(input_data, ensure_ascii=False),
        },
    ]

    result_text = _call_gemma(messages, max_tokens=1000, temperature=0.1)
    return _safe_json_loads(result_text)