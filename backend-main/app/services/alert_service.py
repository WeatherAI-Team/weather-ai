# 탐지 결과 DB 조회를 담당하는 DetectionRepository를 가져와.
# 알림은 detection_events 테이블에서 alert_required=True인 것만 가져올 거야.
# f-024 관리자 알림 내역 / f-014 관리자 알림 위치 표시 / f-013 지역별 알림 현황 
# f-024 관리자 알림 내역 조회
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
    
    # f-014 관리자 알림 위치 표시 API
    def get_admin_alert_map_markers(self):
        # 이 함수는 지도에 표시할 알림 위치 목록을 만들어주는 함수야.
        # 쉽게 말하면 "지도에 찍을 점들만 모아서 보내줘"라는 기능이야.

        # DetectionRepository에게 알림이 필요한 탐지 이벤트만 찾아달라고 부탁해.
        # page=1, per_page=1000으로 많이 가져오는 이유는 지도에 여러 위치를 한 번에 찍기 위해서야.
        alerts = self.detection_repo.find_all(
            page=1,
            per_page=1000,
            alert_required=True
        )

        # 지도에 찍을 수 있는 알림만 담을 빈 리스트를 만들어.
        markers = []

        # 알림 목록을 하나씩 꺼내서 확인해.
        for alert in alerts.items:
            # 위도나 경도가 없으면 지도에 위치를 찍을 수 없어.
            # 그래서 latitude 또는 longitude가 없으면 건너뛰어.
            if alert.latitude is None or alert.longitude is None:
                continue

            # 지도에 필요한 정보만 골라서 markers 리스트에 넣어.
            markers.append({
                # 알림 고유 번호야.
                "id": alert.id,

                # 지도 마커에 보여줄 제목이야.
                # LLM 제목이 있으면 그걸 쓰고, 없으면 기존 이벤트 제목을 써.
                "title": alert.llm_title or alert.event_title,

                # 위치 이름이야.
                # 예: 강남대로, 올림픽대로
                "location_name": alert.location_name,

                # 위도야.
                # DB 숫자 타입을 JSON에서 쓰기 쉽게 float으로 바꿔줘.
                "latitude": float(alert.latitude),

                # 경도야.
                # DB 숫자 타입을 JSON에서 쓰기 쉽게 float으로 바꿔줘.
                "longitude": float(alert.longitude),

                # 위험도 단계야.
                # 지도에서 색깔이나 아이콘을 다르게 보여줄 때 사용할 수 있어.
                "risk_level": alert.risk_level,

                # 위험도 점수야.
                "risk_score": alert.risk_score,

                # 날씨 종류야.
                "weather_type": alert.weather_type,

                # 주요 차량 종류야.
                "main_vehicle_type": alert.main_vehicle_type,

                # 이벤트 상태야.
                "event_status": alert.event_status,

                # 탐지 시간이야.
                "detected_at": alert.detected_at.isoformat() if alert.detected_at else None
            })

        # 지도에 찍을 마커 목록을 돌려줘.
        return markers
    
    # f-013 지역별 알림 현황
    def get_admin_alert_location_summary(self):
        # 이 함수는 지역별 알림 현황을 만들어주는 함수야.
        # 쉽게 말하면 "지역마다 알림이 몇 개 있는지 세어주는 기능"이야.

        # 알림이 필요한 탐지 이벤트만 많이 가져와.
        # alert_required=True는 "관리자 알림 대상만 가져와"라는 뜻이야.
        alerts = self.detection_repo.find_all(
            page=1,
            per_page=1000,
            alert_required=True
        )

        # 지역별로 알림을 모아둘 빈 딕셔너리를 만들어.
        # 예: {"강남대로": {...}, "올림픽대로": {...}} 이런 모양이 될 거야.
        location_summary = {}

        # 알림 목록을 하나씩 꺼내서 확인해.
        for alert in alerts.items:
            # location_name이 없으면 어느 지역인지 알 수 없어.
            # 그래서 위치 이름이 없으면 "위치 미상"으로 넣어.
            location_name = alert.location_name or "위치 미상"

            # 이 지역이 처음 나온 지역이면 기본 값을 만들어줘.
            if location_name not in location_summary:
                location_summary[location_name] = {
                    # 지역 이름이야.
                    "location_name": location_name,

                    # 이 지역의 전체 알림 개수야.
                    "total_alert_count": 0,

                    # 이 지역의 high 위험도 알림 개수야.
                    "high_risk_count": 0,

                    # 이 지역의 medium 위험도 알림 개수야.
                    "medium_risk_count": 0,

                    # 이 지역의 low 위험도 알림 개수야.
                    "low_risk_count": 0,

                    # 지도에서 대표 위치로 쓸 위도야.
                    "latitude": float(alert.latitude) if alert.latitude is not None else None,

                    # 지도에서 대표 위치로 쓸 경도야.
                    "longitude": float(alert.longitude) if alert.longitude is not None else None,

                    # 가장 최근 탐지 시간이야.
                    "latest_detected_at": None
                }

            # 이 지역의 전체 알림 개수를 1개 늘려.
            location_summary[location_name]["total_alert_count"] += 1

            # 위험도별 개수를 세어.
            if alert.risk_level == "high":
                location_summary[location_name]["high_risk_count"] += 1

            elif alert.risk_level == "medium":
                location_summary[location_name]["medium_risk_count"] += 1

            elif alert.risk_level == "low":
                location_summary[location_name]["low_risk_count"] += 1

            # 현재 알림의 탐지 시간이 있으면 최근 시간인지 확인해.
            if alert.detected_at:
                # 기존 최근 시간이 없으면 현재 시간을 넣어.
                if location_summary[location_name]["latest_detected_at"] is None:
                    location_summary[location_name]["latest_detected_at"] = alert.detected_at

                # 기존 시간보다 현재 알림 시간이 더 최신이면 바꿔줘.
                elif alert.detected_at > location_summary[location_name]["latest_detected_at"]:
                    location_summary[location_name]["latest_detected_at"] = alert.detected_at

        # 딕셔너리를 리스트로 바꿔서 프론트가 보기 쉽게 만들어.
        result = []

        for summary in location_summary.values():
            # datetime은 JSON으로 바로 보내기 어려우니까 글자 형태로 바꿔줘.
            if summary["latest_detected_at"]:
                summary["latest_detected_at"] = summary["latest_detected_at"].isoformat()

            # 완성된 지역별 요약 정보를 리스트에 넣어.
            result.append(summary)

        # 알림 개수가 많은 지역부터 보이도록 정렬해.
        result.sort(
            key=lambda item: item["total_alert_count"], # item 하나를 받으면, 그 item 안의 total_alert_count 값을 꺼내줘
            # ex) 강남대로 → 3 올림픽대로 → 7 서초대로 → 1 
            reverse=True # 큰숫자부터 작은 숫자로 정렬  7 → 3 → 1 
        )

        # 지역별 알림 현황 목록을 돌려줘.
        return result

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