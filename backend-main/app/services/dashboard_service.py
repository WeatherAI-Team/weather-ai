# DetectionEvent 모델을 가져와.
# DetectionEvent는 Supabase의 detection_events 테이블과 연결돼.
# f-022 관리자 대시보드
from datetime import datetime, timedelta
from sqlalchemy import func, cast, Date
from ..models.detection_event import DetectionEvent

DAY_LABELS = ['월', '화', '수', '목', '금', '토', '일']


class DashboardService:
    # 이 클래스는 관리자 대시보드에 필요한 통계를 만들어주는 곳이야.
    # 쉽게 말하면 "관리자 화면에 보여줄 숫자들을 계산하는 곳"이야.
    def _to_kst(self, dt):
        # 시간이 없으면 None으로 돌려줘.
        if not dt:
            return None

        # DB에서 UTC처럼 넘어온 시간을 API 응답용 한국 시간으로 바꿔줘.
        return dt + timedelta(hours=9)
    
    def _format_display_time(self, dt):
        # 시간이 없으면 화면에 "-"로 보여줘.
        if not dt:
            return "-"
     
        # DB에는 이미 한국 시간(KST) 기준으로 저장하기 때문에
        # 여기서는 시간을 더하지 않고 그대로 표시만 해.
        return dt.strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")
        
    def get_summary(self):
        # 전체 탐지 이벤트 개수를 세어.
        # detection_events 테이블에 데이터가 몇 개 있는지 확인하는 거야.
        total_event_count = DetectionEvent.query.count()

        # 알림이 필요한 이벤트 개수를 세어.
        # alert_required가 True인 것만 찾는 거야.
        alert_required_count = DetectionEvent.query.filter(
            DetectionEvent.alert_required.is_(True)
        ).count()

        # 고위험 이벤트 개수를 세어.
        # risk_level이 high인 데이터만 찾는 거야.
        high_risk_count = DetectionEvent.query.filter(
            DetectionEvent.risk_level == "high"
        ).count()

        # 오탐 의심 이벤트 개수를 세어.
        # false_positive_suspected가 True인 것만 찾는 거야.
        false_positive_count = DetectionEvent.query.filter(
            DetectionEvent.false_positive_suspected.is_(True)
        ).count()

        # 위험도별 개수를 계산해.
        # 예: high 몇 개, medium 몇 개, low 몇 개
        risk_level_counts = self._count_by_field(DetectionEvent.risk_level)

        # 날씨별 개수를 계산해 (4개 유형 고정 표시, 없으면 0).
        _WEATHER_KEYS = ["clear", "fog", "heavy_rain", "heavy_snow"]
        all_weather = self._count_by_field(DetectionEvent.weather_type)
        normalized = {(k.lower() if k else "unknown"): v for k, v in all_weather.items()}
        weather_type_counts = {k: normalized.get(k, 0) for k in _WEATHER_KEYS}

        # 주요 차량 유형별 개수를 계산해.
        # 예: heavy_truck 몇 개, bus 몇 개
        vehicle_type_counts = self._count_by_field(DetectionEvent.main_vehicle_type)

        # 최근 탐지 이벤트 5개를 가져와.
        # detected_at 기준으로 최신 데이터부터 가져오는 거야.
        recent_events = DetectionEvent.query.order_by(
        DetectionEvent.id.desc()
        ).limit(5).all()

        # 알림 필요 이벤트 최근 5개를 별도로 가져와.
        recent_alert_events = DetectionEvent.query.filter(
        DetectionEvent.alert_required.is_(True)
        ).order_by(
        DetectionEvent.id.desc()
        ).limit(5).all()

        # 계산한 통계들을 딕셔너리 형태로 묶어서 돌려줘.
        # 딕셔너리는 JSON으로 바꾸기 쉬운 모양이야.
        return {
            "total_event_count": total_event_count,
            "alert_required_count": alert_required_count,
            "high_risk_count": high_risk_count,
            "false_positive_count": false_positive_count,
            "risk_level_counts": risk_level_counts,
            "weather_type_counts": weather_type_counts,
            "vehicle_type_counts": vehicle_type_counts,
            "recent_events": [self._event_to_dict(event) for event in recent_events],
            "recent_alert_events": [self._event_to_dict(event) for event in recent_alert_events]
        }

    def _count_by_field(self, field):
        # 이 함수는 특정 컬럼을 기준으로 개수를 세어주는 함수야.
        # 예: risk_level 컬럼이면 high, medium, low가 각각 몇 개인지 세어줘.

        # 결과를 담을 빈 딕셔너리를 만들어.
        # 예: {"high": 3, "medium": 2}
        result = {}

        # 해당 컬럼의 값들을 전부 가져와.
        # 예: risk_level 컬럼이면 high, medium 같은 값들이 나와.
        rows = DetectionEvent.query.with_entities(field).all()

        # 가져온 값을 하나씩 확인해.
        for row in rows:
            # row는 튜플처럼 들어와.
            # row[0]이 실제 컬럼 값이야.
            value = row[0]

            # 값이 비어 있으면 "unknown"으로 표시해.
            # 예: risk_level 값이 없으면 unknown으로 묶어.
            if value is None:
                value = "unknown"

            # 이미 있는 값이면 개수를 1 늘려.
            # 처음 보는 값이면 1로 시작해.
            result[value] = result.get(value, 0) + 1

        # 완성된 개수 결과를 돌려줘.
        return result
    
    def _event_to_dict(self, event):
        # DetectionEvent 객체는 그대로 JSON으로 보내기 어려워.
        # 그래서 필요한 값만 딕셔너리로 바꿔줘.
        kst_detected_at = self._to_kst(event.detected_at)
        return {
            # 탐지 이벤트 고유 번호야.
            "id": event.id,

            # 이벤트 제목이야.
            "event_title": event.event_title,

            # LLM이 만든 제목이야.
            "llm_title": event.llm_title,

            # 이벤트가 발생한 위치 이름이야.
            "location_name": event.location_name,

            # 날씨 유형이야.
            "weather_type": event.weather_type,

            # 주요 차량 유형이야.
            "main_vehicle_type": event.main_vehicle_type,

            # 위험도 점수야.
            "risk_score": event.risk_score,

            # 위험도 등급이야.
            "risk_level": event.risk_level,

            # 이벤트 상태야.
            "event_status": event.event_status,

            # 알림 필요 여부야.
            "alert_required": event.alert_required,
            
            # 탐지 발생 시간이야.
            "detected_at": kst_detected_at.isoformat() if kst_detected_at else None,

            # 화면에 바로 보여줄 한국 시간 값
            # 예: 오후 12:11
            "display_time": self._format_display_time(kst_detected_at)
        }

    def get_weekly_counts(self):
        today = datetime.utcnow().date()
        # 이번 주 월요일 (weekday: 0=월 ~ 6=일)
        monday = today - timedelta(days=today.weekday())

        rows = (DetectionEvent.query
                .with_entities(
                    cast(DetectionEvent.detected_at, Date).label('date'),
                    func.count(DetectionEvent.id).label('count')
                )
                .filter(DetectionEvent.detected_at >= monday)
                .group_by(cast(DetectionEvent.detected_at, Date))
                .all())

        count_by_date = {row.date: row.count for row in rows}

        result = []
        for i in range(7):
            d = monday + timedelta(days=i)
            result.append({
                "date":  d.isoformat(),
                "day":   DAY_LABELS[d.weekday()],
                "count": count_by_date.get(d, 0),
            })
        return result