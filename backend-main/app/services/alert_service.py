# 탐지 결과 DB 조회를 담당하는 DetectionRepository를 가져와.
# 알림은 detection_events 테이블에서 alert_required=True인 것만 가져올 거야.
from ..repositories.detection_repo import DetectionRepository


class AlertService:
    # 이 클래스는 관리자 알림 내역 기능을 처리하는 곳이야.
    # 쉽게 말하면 "알림으로 보여줄 탐지 이벤트만 골라서 정리하는 곳"이야.

    def __init__(self):
        # DetectionRepository를 만들어.
        # detection_events 테이블에서 데이터를 찾기 위해 필요해.
        self.detection_repo = DetectionRepository()

    def get_admin_alerts(self, filters):
        # filters는 사용자가 보낸 검색 조건들이야.
        # 예: 위험도, 날씨, 위치 이름 같은 값들이 들어있어.

        # page는 몇 번째 페이지를 볼지 정하는 값이야.
        # 값이 없으면 1페이지를 보여줘.
        page = filters.get("page", 1)

        # per_page는 한 페이지에 몇 개를 보여줄지 정하는 값이야.
        # 값이 없으면 10개씩 보여줘.
        per_page = filters.get("per_page", 10)

        # DetectionRepository에게 알림이 필요한 탐지 이벤트만 찾아달라고 부탁해.
        # alert_required=True는 "알림이 필요한 것만 가져와"라는 뜻이야.
        alerts = self.detection_repo.find_all(
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
            alert_required=True
        )

        # DB에서 가져온 알림 목록을 프론트가 보기 쉬운 모양으로 바꿔서 돌려줘.
        return {
            # 실제 알림 목록이 들어가는 자리야.
            "items": [self._to_dict(alert) for alert in alerts.items],

            # 페이지 정보를 담는 자리야.
            "pagination": {
                "page": alerts.page,
                "per_page": alerts.per_page,
                "total": alerts.total,
                "pages": alerts.pages
            }
        }

    def get_admin_alert_detail(self, alert_id):
        # alert_id는 API 주소에서 받은 알림 번호야.
        # 사실 이 번호는 detection_events 테이블의 id야.
        # 예: /api/admin/alerts/1 이면 alert_id는 1이야.

        # DetectionRepository에게 id에 맞는 탐지 이벤트 1개를 찾아달라고 부탁해.
        alert = self.detection_repo.find_by_id(alert_id)

        # 해당 id의 데이터가 없으면 None을 돌려줘.
        if alert is None:
            return None

        # 데이터는 있지만 알림 대상이 아니면 None을 돌려줘.
        # alert_required가 True인 것만 관리자 알림으로 보여줄 거야.
        if alert.alert_required is not True:
            return None

        # 찾은 알림 데이터를 프론트가 보기 쉬운 딕셔너리 모양으로 바꿔서 돌려줘.
        return self._to_dict(alert)

    def _to_dict(self, alert):
        # DB에서 가져온 DetectionEvent 객체는 그대로 JSON으로 보내기 어려워.
        # 그래서 필요한 값만 딕셔너리 모양으로 바꿔줘.

        return {
            # 알림 고유 번호야.
            # 실제로는 detection_events 테이블의 id야.
            "id": alert.id,

            # 알림 제목이야.
            # LLM 제목이 있으면 그걸 먼저 쓰고, 없으면 event_title을 써.
            "title": alert.llm_title or alert.event_title,

            # 알림 요약 내용이야.
            "summary": alert.llm_summary,

            # 이벤트가 발생한 위치 이름이야.
            "location_name": alert.location_name,

            # 위도야.
            # 지도에서 위치를 표시할 때 필요해.
            "latitude": float(alert.latitude) if alert.latitude is not None else None,

            # 경도야.
            # 지도에서 위치를 표시할 때 필요해.
            "longitude": float(alert.longitude) if alert.longitude is not None else None,

            # 날씨 종류야.
            # 예: rain, snow
            "weather_type": alert.weather_type,

            # 주요 차량 종류야.
            # 예: heavy_truck
            "main_vehicle_type": alert.main_vehicle_type,

            # 위험도 점수야.
            "risk_score": alert.risk_score,

            # 위험도 단계야.
            # 예: low, medium, high
            "risk_level": alert.risk_level,

            # 이벤트 상태야.
            # 예: pending, confirmed, resolved
            "event_status": alert.event_status,

            # 알림 필요 여부야.
            # 여기서는 보통 True일 거야.
            "alert_required": alert.alert_required,

            # LLM 판단 결과야.
            "llm_decision": alert.llm_decision,

            # LLM 판단 이유야.
            "llm_reason": alert.llm_reason,

            # 오탐 의심 여부야.
            "false_positive_suspected": alert.false_positive_suspected,

            # 탐지된 시간이야.
            "detected_at": alert.detected_at.isoformat() if alert.detected_at else None,

            # 데이터가 만들어진 시간이야.
            "created_at": alert.created_at.isoformat() if alert.created_at else None,

            # 데이터가 수정된 시간이야.
            "updated_at": alert.updated_at.isoformat() if alert.updated_at else None
        }