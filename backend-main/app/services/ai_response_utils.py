# app/services/ai_response_utils.py
# backend-ai 응답을 backend-main 전반에서 통일된 형태로 다루기 위한 공용 유틸.


def to_ratio(value):
    """
    AI 서버에서 받은 confidence 값을 0~1 범위 비율로 변환한다.

    backend-ai 응답이 91.0처럼 퍼센트 값으로 올 수도 있고,
    0.91처럼 이미 비율 값으로 올 수도 있기 때문에
    backend-main에서 통일된 형태로 맞춘다.
    """

    # 값이 없으면 그대로 None 반환
    if value is None:
        return None

    try:
        # 문자열/정수/실수 형태를 모두 float으로 변환 시도
        value = float(value)
    except Exception:
        # 숫자로 바꿀 수 없는 값이면 None 처리
        return None

    # 1보다 크면 91.0 같은 퍼센트 값으로 보고 100으로 나눔
    if value > 1:
        return round(value / 100, 4)

    # 이미 0~1 사이 값이면 그대로 사용
    return round(value, 4)
