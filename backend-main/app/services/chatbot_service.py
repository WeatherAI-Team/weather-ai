# 탐지 결과를 조회하는 Repository를 가져와.
# 챗봇이 "강남 위험해?" 같은 질문에 답하려면 탐지 데이터를 확인해야 해.
# f-026 AI chatbot
from ..repositories.detection_repo import DetectionRepository


class ChatbotService:
    # 이 클래스는 챗봇 답변을 만드는 곳이야.
    # 쉽게 말하면 "사용자 질문을 보고 어떤 답을 할지 정하는 곳"이야.

    def __init__(self):
        # DetectionRepository를 만들어.
        # 이제 챗봇도 detection_events 테이블의 데이터를 볼 수 있어.
        self.detection_repo = DetectionRepository()

    def create_response(self, message):
        # message는 사용자가 보낸 질문이야.
        # 예: "강남대로 위험해?"

        # 질문이 비어 있으면 안내 메시지를 돌려줘.
        if not message:
            return {
                "intent": "empty_message",
                "answer": "질문 내용을 입력해 주세요.",
                "data": None
            }

        # 질문 앞뒤에 있는 쓸데없는 공백을 없애.
        # 예: "  강남 위험해?  " → "강남 위험해?"
        message = message.strip()

        # 질문의 의도를 간단하게 파악해.
        # 예: 위험 상태 질문인지, 사용법 질문인지 구분해.
        intent = self._detect_intent(message)

        # 사용자가 위험 상태를 물어본 경우야.
        if intent == "risk_status":
            return self._handle_risk_status(message)

        # 사용자가 서비스 사용법을 물어본 경우야.
        if intent == "service_help":
            return self._handle_service_help()

        # 사용자가 CCTV 관련 질문을 한 경우야.
        if intent == "cctv_help":
            return self._handle_cctv_help()

        # 위 조건에 해당하지 않으면 기본 답변을 해.
        return {
            "intent": "unknown",
            "answer": "죄송합니다. 질문을 정확히 이해하지 못했습니다. 지역 위험 상태, CCTV 확인 방법, 서비스 사용법에 대해 질문해 주세요.",
            "data": None
        }

    def _detect_intent(self, message):
        # 이 함수는 사용자의 질문이 어떤 종류인지 간단히 판단해.
        # 아직 LLM을 붙이지 않았기 때문에 단어 포함 여부로 판단해.

        # 위험 상태를 묻는 단어들이 들어 있으면 risk_status로 판단해.
        risk_keywords = ["위험", "위험해", "상태", "괜찮", "사고", "알림", "탐지"]

        # 서비스 사용법 관련 단어들이 들어 있으면 service_help로 판단해.
        help_keywords = ["사용법", "어떻게", "이용", "서비스", "기능", "도움"]

        # CCTV 관련 단어들이 들어 있으면 cctv_help로 판단해.
        cctv_keywords = ["cctv", "CCTV", "카메라", "영상"]

        # 위험 관련 단어가 질문에 하나라도 들어 있으면 위험 상태 질문으로 봐.
        if any(keyword in message for keyword in risk_keywords):
            return "risk_status"

        # CCTV 관련 단어가 질문에 하나라도 들어 있으면 CCTV 안내 질문으로 봐.
        if any(keyword in message for keyword in cctv_keywords):
            return "cctv_help"

        # 사용법 관련 단어가 질문에 하나라도 들어 있으면 서비스 안내 질문으로 봐.
        if any(keyword in message for keyword in help_keywords):
            return "service_help"

        # 아무 조건에도 맞지 않으면 알 수 없는 질문으로 봐.
        return "unknown"

    def _extract_location_name(self, message):
        # 이 함수는 질문에서 지역명이나 도로명을 뽑아내는 함수야. → 질문에서 지역/도로명만 뽑기
        # 예: "강남대로 위험해?" -> "강남대로"

        # 사용자가 실수로 글자 사이에 띄어쓰기를 넣을 수 있어.
        # 예: "강 남대로" -> "강남대로"
        # 그래서 먼저 모든 공백을 없앤 문장을 만들어.
        compact_message = message.replace(" ", "")

        # 질문에서 빼고 싶은 말들이야.
        # 이런 단어들은 위치 이름이 아니라 질문 표현이기 때문에 제거해.
        remove_words = [
            "위험해",
            "위험한가요",
            "위험한가",
            "위험",
            "상태",
            "알려줘",
            "알려주세요",
            "어때",
            "어떤가요",
            "괜찮아",
            "괜찮나요",
            "사고",
            "알림",
            "탐지",
            "도로상황",
            "상황",
            "지금",
            "현재",
            "오늘",
            "근처",
            "쪽",
            "는",
            "은",
            "이",
            "가",
            "?"
        ]

        # 공백을 제거한 문장을 위치 이름 후보로 사용해.
        location_name = compact_message

        # 필요 없는 단어들을 하나씩 제거해.
        for word in remove_words:
            location_name = location_name.replace(word, "")

        # 앞뒤 빈칸을 제거해.
        location_name = location_name.strip()

        # 아무것도 남지 않으면 None을 돌려줘.
        if not location_name:
            return None

        # 뽑아낸 위치 이름을 돌려줘.
        return location_name

    def _make_risk_answer(self, location_name, matched_count, latest_event):
        # 이 함수는 위험도에 따라 챗봇 답변 문장을 다르게 만들어주는 함수야. → 위험도에 따라 답변 문장 만들기
        # 예: high면 더 강한 주의 문구를 보여줘.

        # 최근 이벤트의 위험도 등급을 가져와.
        # 값이 없으면 unknown으로 처리해.
        risk_level = latest_event.get("risk_level") or "unknown"

        # 최근 이벤트의 위험도 점수를 가져와.
        risk_score = latest_event.get("risk_score")

        # 위험도 점수가 있으면 문장에 넣을 수 있게 준비해.
        if risk_score is not None:
            score_text = f"위험도 점수는 {risk_score}점입니다."
        else:
            score_text = "위험도 점수는 확인되지 않았습니다."

        # 위험도가 high이면 강한 주의 문구를 만들어.
        if risk_level == "high":
            return f"{location_name}에서 고위험 알림이 {matched_count}건 확인되었습니다. 주의가 필요합니다. {score_text}"

        # 위험도가 medium이면 주의 단계 문구를 만들어.
        if risk_level == "medium":
            return f"{location_name}에서 주의 단계의 위험 알림이 {matched_count}건 확인되었습니다. {score_text}"

        # 위험도가 low이면 낮은 위험도 문구를 만들어.
        if risk_level == "low":
            return f"{location_name}에서 낮은 위험도의 알림이 {matched_count}건 확인되었습니다. {score_text}"

        # 위험도 값이 high, medium, low 중 하나가 아니면 기본 문구를 만들어.
        return f"{location_name}에서 위험 알림이 {matched_count}건 확인되었습니다. {score_text}"


    def _handle_risk_status(self, message):
        # 이 함수는 특정 지역/도로 위험 상태 질문에 답하는 함수야. → 위험 상태 질문 전체 처리 담당
        # 예: "강남대로 위험해?"

        # 질문에서 지역명 또는 도로명을 뽑아.
        location_name = self._extract_location_name(message)

        # 지역명이나 도로명이 없으면 다시 입력하라고 안내해.
        if location_name is None:
            return {
                "intent": "risk_status",
                "location_name": None,
                "answer": "확인할 지역명이나 도로명을 함께 입력해 주세요. 예: '강남대로 위험해?'",
                "data": None
            }

        # detection_events 테이블에서 해당 위치의 알림 필요 이벤트를 찾아.
        # alert_required=True는 실제 알림이 필요한 이벤트만 보겠다는 뜻이야.
        detections = self.detection_repo.find_all(
            page=1,
            per_page=5,
            location_name=location_name,
            alert_required=True
        )

        # 해당 위치에 위험 알림이 없으면 안내해.
        if detections.total == 0:
            return {
                "intent": "risk_status",
                "location_name": location_name,
                "answer": f"현재 {location_name} 관련 위험 알림은 확인되지 않았습니다.",
                "data": {
                    "matched_count": 0,
                    "events": []
                }
            }

        # 위험 알림이 있으면 프론트가 보기 쉽게 정리해.
        events = []

        # 조회된 이벤트를 하나씩 꺼내서 필요한 정보만 담아.
        for detection in detections.items:
            events.append({
            # 탐지 이벤트 고유 번호야.
            "id": detection.id,

            # 이벤트 위치 이름이야.
            "location_name": detection.location_name,

            # 위험도 등급이야.
            "risk_level": detection.risk_level,

            # 위험도 점수야.
            "risk_score": detection.risk_score,

            # 알림 제목이야.
            "title": detection.llm_title or detection.event_title,

            # 알림 요약이야.
            "summary": detection.llm_summary,

            # 날씨 유형이야.
            "weather_type": detection.weather_type,

            # 주요 차량 유형이야.
            "main_vehicle_type": detection.main_vehicle_type,

            # 위도야.
            # 프론트에서 지도 위치를 표시할 때 사용할 수 있어.
            "latitude": float(detection.latitude) if detection.latitude is not None else None,

            # 경도야.
            # 프론트에서 지도 위치를 표시할 때 사용할 수 있어.
            "longitude": float(detection.longitude) if detection.longitude is not None else None,

            # 관리자 알림 상세 조회 API 주소야.
            # 프론트에서 "상세 보기" 버튼을 만들 때 사용할 수 있어.
            "alert_detail_api": f"/api/admin/alerts/{detection.id}",

            # 지도 알림 위치 조회 API 주소야.
            # 프론트에서 "지도에서 보기" 버튼을 만들 때 사용할 수 있어.
            "map_api": "/api/admin/alerts/map",

            # 탐지 발생 시간이야.
            "detected_at": detection.detected_at.isoformat() if detection.detected_at else None
        })

        # 가장 최근 이벤트 하나를 기준으로 답변을 만들어.
        latest_event = events[0]

        # 위험도에 따라 다른 답변 문장을 만들어.
        answer = self._make_risk_answer(
            location_name=location_name,
            matched_count=detections.total,
            latest_event=latest_event
        )

        # 챗봇 답변 결과를 돌려줘.
        return {
            # 질문 의도는 특정 지역/도로 위험 상태 확인이야.
            "intent": "risk_status",

            # 질문에서 뽑아낸 위치 이름이야.
            "location_name": location_name,

            # 위험도에 따라 만들어진 답변 문장이야.
            "answer": answer,

            # 프론트에서 추가로 쓸 수 있는 데이터야.
           "data": {
                # 관련 위험 알림 개수야.
                "matched_count": detections.total,

                # 최근 위험도 등급이야.
                "latest_risk_level": latest_event.get("risk_level"),

                # 최근 위험도 점수야.
                "latest_risk_score": latest_event.get("risk_score"),

                # 가장 최근 알림 상세 조회 API 주소야.
                # 프론트에서 대표 상세 보기 버튼에 연결할 수 있어.
                "latest_alert_detail_api": latest_event.get("alert_detail_api"),

                # 관리자 알림 지도 위치 조회 API 주소야.
                # 프론트에서 지도 보기 버튼에 연결할 수 있어.
                "map_api": "/api/admin/alerts/map",

                # 관련 이벤트 목록이야.
                "events": events
            }
        }
    
    def _handle_service_help(self):
        # 이 함수는 서비스 사용법 질문에 답하는 곳이야.

        return {
            "intent": "service_help",
            "answer": "Weather-AI는 악천후 상황에서 CCTV 기반 탐지 결과를 확인하고, 위험 차량 이벤트와 관리자 알림을 조회할 수 있는 서비스입니다.",
            "data": None
        }

    def _handle_cctv_help(self):
        # 이 함수는 CCTV 확인 방법 질문에 답하는 곳이야.

        return {
            "intent": "cctv_help",
            "answer": "CCTV 정보는 지도 화면 또는 CCTV 목록 화면에서 확인할 수 있습니다. 지역이나 도로명을 기준으로 관련 이벤트 위치도 함께 확인할 수 있습니다.",
            "data": None
        }