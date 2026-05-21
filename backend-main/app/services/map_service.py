# 탐지 이벤트 DB 조회를 담당하는 DetectionRepository를 가져와.
# 지도에는 detection_events 테이블에 있는 위치 정보를 표시할 거야.
# f-012 지도 API 연동
from ..repositories.detection_repo import DetectionRepository


class MapService:
    # 이 클래스는 지도에 필요한 데이터를 만들어주는 곳이야.
    # 쉽게 말하면 "지도에 찍을 점들을 정리하는 곳"이야.

    def __init__(self):
        # DetectionRepository를 만들어.
        # 이제 detection_events 테이블에서 데이터를 가져올 수 있어.
        self.detection_repo = DetectionRepository()

    def get_event_markers(self, filters):
        # filters는 사용자가 보낸 검색 조건들이야.
        # 예: 위험도, 날씨, 차량 종류 같은 값들이 들어있어.

        # page는 몇 번째 페이지인지 정하는 값이야.
        # 지도는 여러 점을 한 번에 보여줘야 하니까 기본은 1페이지로 해.
        page = filters.get("page", 1)

        # per_page는 한 번에 몇 개를 가져올지 정하는 값이야.
        # 지도 마커는 많이 필요할 수 있어서 기본 100개로 잡아.
        per_page = filters.get("per_page", 100)

        # Repository에게 조건에 맞는 탐지 이벤트를 찾아달라고 부탁해.
        events = self.detection_repo.find_all(
            page=page,
            per_page=per_page,
            keyword=filters.get("keyword"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            location_name=filters.get("location_name"),
            weather_type=filters.get("weather_type"),
            risk_level=filters.get("risk_level"),
            main_vehicle_type=filters.get("main_vehicle_type"),
            event_status=filters.get("event_status"),
            time_type=filters.get("time_type"),
            alert_required=filters.get("alert_required")
        )

        # 지도에 표시할 마커들을 담을 빈 리스트를 만들어.
        markers = []

        # 탐지 이벤트 목록을 하나씩 확인해.
        for event in events.items:
            # 위도나 경도가 없으면 지도에 점을 찍을 수 없어.
            # 그래서 둘 중 하나라도 없으면 건너뛰어.
            if event.latitude is None or event.longitude is None:
                continue

            # 지도에 필요한 정보만 골라서 markers 리스트에 넣어.
            markers.append({
                # 탐지 이벤트 고유 번호야.
                "id": event.id,

                # 지도 마커에 보여줄 제목이야.
                # LLM 제목이 있으면 그걸 쓰고, 없으면 기본 이벤트 제목을 써.
                "title": event.llm_title or event.event_title,

                # 위치 이름이야.
                "location_name": event.location_name,

                # 위도야.
                # DB 숫자 타입을 JSON에서 쓰기 쉽게 float으로 바꿔줘.
                "latitude": float(event.latitude),

                # 경도야.
                # DB 숫자 타입을 JSON에서 쓰기 쉽게 float으로 바꿔줘.
                "longitude": float(event.longitude),

                # 날씨 유형이야.
                "weather_type": event.weather_type,

                # 주요 차량 유형이야.
                "main_vehicle_type": event.main_vehicle_type,

                # 위험도 점수야.
                "risk_score": event.risk_score,

                # 위험도 등급이야.
                "risk_level": event.risk_level,

                # 이벤트 처리 상태야.
                "event_status": event.event_status,

                # 알림 필요 여부야.
                "alert_required": event.alert_required,

                # 탐지 발생 시간이야.
                "detected_at": event.detected_at.isoformat() if event.detected_at else None
            })

        # 지도 마커 목록과 페이지 정보를 같이 돌려줘.
        return {
            "items": markers,
            "pagination": {
                "page": events.page,
                "per_page": events.per_page,
                "total": events.total,
                "pages": events.pages
            }
        }