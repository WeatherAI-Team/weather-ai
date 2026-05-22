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

        # message가 None이면 빈 문자열로 바꿔.
        # 예: 프론트에서 message를 안 보낸 경우를 대비하는 거야.
        if message is None:
            message = ""

        # 질문 앞뒤에 있는 쓸데없는 공백을 먼저 없애.
        # 예: "  강남 위험해?  " → "강남 위험해?"
        message = message.strip()

        # 공백을 지운 뒤에도 질문이 비어 있으면 안내 메시지를 돌려줘.
        # 예: "     " → "" 이 되니까 여기서 걸러져.
        if not message:
            return {
                "intent": "empty_message",
                "answer": "질문 내용을 입력해 주세요.",
                "data": None
            }

        # 질문의 의도를 간단하게 파악해.
        # 예: 위험 상태 질문인지, 사용법 질문인지 구분해.
        intent = self._detect_intent(message)

        # 사용자가 Weather-AI 프로젝트 설명을 물어본 경우야.
        if intent == "project_help":
            return self._handle_project_help()

        # 사용자가 위험 차량이나 탐지 차량을 물어본 경우야.
        if intent == "vehicle_help":
            return self._handle_vehicle_help()

        # 사용자가 위험도 점수나 LLM 검증을 물어본 경우야.
        if intent == "risk_score_help":
            return self._handle_risk_score_help()

        # 사용자가 관리자 기능을 물어본 경우야.
        if intent == "admin_help":
            return self._handle_admin_help()

        # 사용자가 탐지 날씨 조건을 물어본 경우야.
        if intent == "weather_help":
            return self._handle_weather_help()

        # 사용자가 위험 상태를 물어본 경우야.
        if intent == "risk_status":
            return self._handle_risk_status(message)

        # 사용자가 서비스 사용법을 물어본 경우야.
        if intent == "service_help":
            return self._handle_service_help()

        # 사용자가 CCTV 관련 질문을 한 경우야.
        if intent == "cctv_help":
            return self._handle_cctv_help()

        # 사용자가 알림 기준이나 알림 방법을 물어본 경우야.
        if intent == "notification_help":
            return self._handle_notification_help()

        # 위 조건에 해당하지 않으면 추천 질문을 포함한 기본 답변을 해.
        return self._handle_unknown()

    def _detect_intent(self, message):
        # 비교를 쉽게 하기 위해 소문자로 바꿔.
        # 영어 CCTV/cctv, Weather-AI/weather-ai, heavy truck/Heavy Truck 구분을 줄이기 위한 처리야.
        lower_message = message.lower()

        # 위험도 점수나 LLM 검증 질문을 먼저 확인해.
        # 예: "위험도 점수는 뭐야?", "LLM 검증은 뭐야?", "오탐은 어떻게 줄여?"
        # 이걸 먼저 확인해야 "위험도 점수는 뭐야?"가 risk_status나 project_help로 잘못 가지 않아.
        risk_score_keywords = [
            "위험도 점수",
            "위험도",
            "점수",
            "llm",
            "검증",
            "필터링",
            "오탐",
            "오탐지",
            "위험 기준",
            "위험 판단",
            "위험하게 판단",
            "점수 기준",
            "점수 계산",
            "어떻게 계산",
            "위험도 계산",
            "위험도 기준",
            "llm 검증",
            "2차 검증",
            "1차 필터링"
        ]

        # 질문 안에 위험도 점수나 LLM 검증 관련 단어가 있으면 risk_score_help로 판단해.
        if any(keyword in lower_message for keyword in risk_score_keywords):
            return "risk_score_help"

        # Weather-AI 서비스 전체 설명 질문을 확인해.
        # 예: "Weather-AI가 뭐야?", "날씨의아이는 어떤 시스템이야?", "ai서비스가 뭐야?"
        project_keywords = [
            "weather-ai",
            "weather ai",
            "날씨의아이",
            "이 시스템",
            "이 서비스",
            "ai서비스",
            "ai 서비스",
            "인공지능 서비스",
            "뭐하는 서비스",
            "무슨 서비스",
            "서비스 소개",
            "시스템 소개",
            "프로젝트 설명",
            "프로젝트가 뭐야",
            "시스템이 뭐야",
            "어떤 시스템",
            "어떤 서비스",
            "서비스 목적",
            "프로젝트 목적"
        ]

        # 질문 안에 프로젝트 설명 관련 단어가 하나라도 있으면 project_help로 판단해.
        if any(keyword in lower_message for keyword in project_keywords):
            return "project_help"

        # 차량 분류나 탐지 차량 질문을 확인해.
        # 예: "어떤 차량을 탐지해?", "무슨 차량을 탐지해?", "heavy truck 기준이 뭐야?"
        vehicle_keywords = [
            "위험 차량",
            "차량 기준",
            "heavy truck",
            "헤비트럭",
            "25톤",
            "카고트럭",
            "카고 트럭",
            "탱크로리",
            "레미콘",
            "어떤 차량",
            "무슨 차량",
            "차량 탐지",
            "탐지 차량",
            "탐지 가능한 차량",
            "차량 종류",
            "탐지할 수",
            "탐지 할 수",
            "인식하는 차량",
            "잡아내는 차량",
            "잡아내는 대상",
            "도로에서 잡아내는",
            "탐지 대상",
            "인식 대상",
            "무엇을 탐지",
            "뭘 탐지",
            "뭐를 탐지"
        ]

        # 질문 안에 차량 관련 단어가 하나라도 있으면 vehicle_help로 판단해.
        if any(keyword in lower_message for keyword in vehicle_keywords):
            return "vehicle_help"

        # 관리자 기능 질문을 확인해.
        # 예: "관리자는 뭘 확인할 수 있어?", "대시보드에서 뭐 볼 수 있어?"
        admin_keywords = [
            "관리자",
            "대시보드",
            "알림 내역",
            "통계",
            "사용자 조회",
            "사용자 목록",
            "관리 기능",
            "관리자 기능",
            "관리 화면",
            "관리자 화면",
            "관리자는",
            "뭘 확인",
            "뭐 볼 수",
            "조회할 수"
        ]

        # 질문 안에 관리자 기능 관련 단어가 있으면 admin_help로 판단해.
        if any(keyword in lower_message for keyword in admin_keywords):
            return "admin_help"

        # 탐지하는 날씨 조건 질문을 확인해.
        # 예: "어떤 날씨를 탐지해?", "폭우랑 폭설도 탐지해?", "안개도 포함돼?"
        weather_keywords = [
            "어떤 날씨",
            "무슨 날씨",
            "날씨 탐지",
            "날씨 조건",
            "폭우",
            "폭설",
            "악천후",
            "야간",
            "주간",
            "안개",
            "비와",
            "비가",
            "눈이",
            "눈와",
            "비 오는",
            "눈 오는",
            "밤에도",
            "낮에도",
            "기상 조건",
            "도로 환경"
        ]

        # 질문 안에 날씨 조건 관련 단어가 있으면 weather_help로 판단해.
        if any(keyword in lower_message for keyword in weather_keywords):
            return "weather_help"

        # CCTV 관련 질문을 확인해.
        # 예: "CCTV는 어디서 볼 수 있어?", "카메라 영상은 어디 있어?"
        cctv_keywords = [
            "cctv",
            "카메라",
            "영상",
            "cctv 확인",
            "영상 확인",
            "카메라 확인",
            "어디서 봐",
            "어디서 볼",
            "화면 확인",
            "도로 영상"
        ]

        # 질문 안에 CCTV 관련 단어가 있으면 cctv_help로 판단해.
        if any(keyword in lower_message for keyword in cctv_keywords):
            return "cctv_help"

        # 알림 안내 질문을 확인해.
        # 예: "알림은 언제 와?", "알림 기준이 뭐야?"
        notification_keywords = [
            "알림 언제",
            "알림 기준",
            "알림 오",
            "알림 받",
            "알림은",
            "알림 있어",
            "알림 확인",
            "알림 보는",
            "알림 조회",
            "언제 알려줘",
            "언제 알림",
            "경고 알림",
            "위험 알림",
            "알림 발생",
            "알림 조건"
        ]

        # 질문 안에 알림 관련 단어가 있으면 notification_help로 판단해.
        if any(keyword in lower_message for keyword in notification_keywords):
            return "notification_help"

        # 위험 상태 질문을 확인해.
        # 예: "강남대로 위험해?", "현재 도로 상태 알려줘"
        risk_keywords = [
            "위험",
            "위험해",
            "상태",
            "괜찮",
            "사고",
            "탐지"
        ]

        # 질문 안에 위험 상태 관련 단어가 있으면 risk_status로 판단해.
        if any(keyword in lower_message for keyword in risk_keywords):
            return "risk_status"

        # 서비스 사용법 질문을 확인해.
        # 예: "서비스 사용법 알려줘", "어떻게 이용해?"
        help_keywords = [
            "사용법",
            "어떻게",
            "이용",
            "기능",
            "도움"
        ]

        # 질문 안에 사용법 관련 단어가 있으면 service_help로 판단해.
        if any(keyword in lower_message for keyword in help_keywords):
            return "service_help"

        # 아무 조건에도 맞지 않으면 알 수 없는 질문으로 판단해.
        return "unknown"

    def _handle_project_help(self):
        # 이 함수는 Weather-AI 서비스가 무엇인지 설명하는 곳이야.

        return {
            "intent": "project_help",
            "answer": "Weather-AI는 폭우·폭설 같은 악천후와 주간·야간 도로 환경에서 CCTV 영상을 AI로 분석해 위험 차량과 도로 위험 이벤트를 탐지하고, 관리자에게 알림을 제공하는 교통 안전 관제 시스템입니다.",
            "data": None
        }

    def _handle_vehicle_help(self):
        # 이 함수는 위험 차량과 탐지 차량 기준을 설명하는 곳이야.

        return {
            "intent": "vehicle_help",
            "answer": "Weather-AI는 레미콘, 카고트럭, 25톤 이상의 화물차량, 탱크로리 등 위험 차량을 탐지합니다. 프로젝트 기준에서 25톤 이상의 화물차량은 heavy truck으로 분류하며, 레미콘·카고트럭·탱크로리는 heavy truck 클래스에 포함하지 않고 별도 차량 클래스로 구분합니다.",
            "data": None
        }

    def _handle_risk_score_help(self):
        # 이 함수는 위험도 점수와 LLM 검증 과정을 설명하는 곳이야.

        return {
            "intent": "risk_score_help",
            "answer": "위험도 점수는 탐지된 차량 유형, 날씨 상황, 도로 환경, 알림 필요 여부 등을 기준으로 위험 가능성을 수치화한 값입니다. Weather-AI는 1차로 위험도 점수를 계산하고, 2차로 LLM 검증을 통해 실제 위험 가능성이 높은 이벤트를 선별합니다.",
            "data": None
        }

    def _handle_admin_help(self):
        # 이 함수는 관리자가 확인할 수 있는 기능을 설명하는 곳이야.

        return {
            "intent": "admin_help",
            "answer": "관리자는 대시보드에서 탐지 이벤트 현황, 지역별 알림, 위험도 통계, 사용자 정보, 과거 알림 내역을 확인할 수 있습니다. 또한 지도에서 CCTV 위치와 위험 이벤트 발생 위치를 확인할 수 있습니다.",
            "data": None
        }

    def _handle_weather_help(self):
        # 이 함수는 Weather-AI가 다루는 날씨와 도로 환경 조건을 설명하는 곳이야.

        return {
            "intent": "weather_help",
            "answer": "현재 Weather-AI의 MVP 범위는 폭우와 폭설 상황을 중심으로 하며, 주간과 야간 도로 환경을 함께 고려합니다. 안개와 복원 탐지는 MVP 범위에서 제외했습니다.",
            "data": None
        }

    def _handle_notification_help(self):
        # 이 함수는 알림 기준이나 알림 방식에 대한 질문에 답하는 곳이야.

        return {
            "intent": "notification_help",
            "answer": "위험도 기준 이상으로 판단된 이벤트가 발생하면 관리자에게 알림이 전달됩니다. 알림은 위험도 점수와 LLM 검증 결과를 기준으로 선별됩니다.",
            "data": None
        }

    def _handle_unknown(self):
        # 이 함수는 챗봇이 질문을 이해하지 못했을 때 실행돼.
        # 그냥 "모르겠다"만 말하지 않고, 사용자가 다시 질문할 수 있게 예시 질문을 알려줘.

        return {
            "intent": "unknown",
            "answer": "질문을 정확히 이해하지 못했습니다. 아래 예시처럼 질문해 보세요.",
            "data": {
                "suggestions": [
                    "Weather-AI가 뭐야?",
                    "어떤 차량을 탐지해?",
                    "위험도 점수는 뭐야?",
                    "LLM 검증은 뭐야?",
                    "관리자는 뭘 확인할 수 있어?",
                    "어떤 날씨를 탐지해?",
                    "CCTV는 어디서 볼 수 있어?",
                    "알림은 언제 와?",
                    "강남대로 위험해?"
                ]
            }
        }

    def _extract_location_name(self, message):
        # 질문에서 지역명이나 도로명을 뽑아내는 함수야.
        # 예: "강남대로 위험해?" -> "강남대로"

        # 앞뒤 공백을 없애.
        location_name = message.strip()

        # 질문에서 제거할 문장 표현들이야.
        # 위치 이름이 아니라 질문 표현이기 때문에 빼줘.
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
            "?"
        ]

        # 필요 없는 표현을 제거해.
        for word in remove_words:
            location_name = location_name.replace(word, "")

        # 앞뒤 공백을 제거해.
        location_name = location_name.strip()

        # 끝에 붙은 조사만 제거해.
        # 예: "강남대로는" -> "강남대로"
        # 단어 중간의 "가", "이"는 건드리지 않아.
        for particle in ["은", "는", "이", "가"]:
            if location_name.endswith(particle):
                location_name = location_name[:-1]

        # 다시 앞뒤 공백을 제거해.
        location_name = location_name.strip()

        # 아무것도 남지 않으면 None을 돌려줘.
        if not location_name:
            return None

        # 뽑아낸 위치 이름을 돌려줘.
        return location_name

    def _make_risk_answer(self, location_name, matched_count, latest_event):
        # 이 함수는 위험도에 따라 챗봇 답변 문장을 다르게 만들어주는 함수야.
        # 예: high면 더 강한 주의 문구를 보여줘.

        # 최근 이벤트의 위험도 등급을 가져와.
        # 값이 없으면 unknown으로 처리해.
        risk_level = (latest_event.get("risk_level") or "unknown").lower()

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
        # 이 함수는 특정 지역/도로 위험 상태 질문에 답하는 함수야.
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