# 탐지 이벤트 DB 조회를 담당하는 Repository를 가져와.
# Repository는 DB에서 데이터를 찾아오는 역할을 해.
from ..repositories.detection_repo import DetectionRepository


class DetectionService:
    # 이 클래스는 탐지 결과 기능을 처리하는 중간 관리자야.
    # 쉽게 말하면 API와 DB 사이에서 데이터를 정리해주는 역할을 해.

    def __init__(self):
        # DetectionRepository를 만들어.
        # 이제 이 service 안에서 DB 조회 기능을 사용할 수 있어.
        self.detection_repo = DetectionRepository()

    def get_detections(self, filters):
        # filters는 API에서 받은 검색 조건들이야.
        # 예: 위험도, 날씨, 위치 이름 같은 값들이 들어있어.

        # page는 몇 번째 페이지를 볼지 정하는 값이야.
        # 값이 없으면 1페이지를 보여줘.
        page = filters.get("page", 1)

        # per_page는 한 페이지에 몇 개를 보여줄지 정하는 값이야.
        # 값이 없으면 10개씩 보여줘.
        per_page = filters.get("per_page", 10)

        # Repository에게 조건에 맞는 탐지 이벤트를 찾아달라고 부탁해.
        detections = self.detection_repo.find_all(
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

        # DB에서 가져온 결과를 프론트가 보기 쉬운 모양으로 바꿔서 돌려줘.
        return {
            # 실제 탐지 이벤트 목록이 들어가는 자리야.
            "items": [self._to_dict(detection) for detection in detections.items],

            # 페이지 정보를 담는 자리야.
            # 프론트에서 현재 페이지, 전체 개수, 전체 페이지 수를 알 수 있어.
            "pagination": {
                "page": detections.page,
                "per_page": detections.per_page,
                "total": detections.total,
                "pages": detections.pages
            }
        }
    def get_detection_detail(self, detection_id):
    # detection_id는 API에서 받은 탐지 이벤트 번호야.
    # 예: /api/detections/1 이면 detection_id는 1이야.

        # Repository에게 id에 맞는 탐지 이벤트 1개를 찾아달라고 부탁해.
        detection = self.detection_repo.find_by_id(detection_id)

        # 만약 해당 id의 탐지 이벤트가 없으면 None을 돌려줘.
        if detection is None:
            return None

        # 찾은 탐지 이벤트를 딕셔너리로 바꿔서 돌려줘.
        return self._to_dict(detection)
    
    def _to_dict(self, detection):
        # DB에서 가져온 DetectionEvent 객체는 그대로 JSON으로 보내기 어려워.
        # 그래서 프론트가 받기 쉬운 딕셔너리 모양으로 바꿔줘.

        return {
            # 탐지 이벤트 고유 번호
            "id": detection.id,

            # 어떤 CCTV에서 발생한 이벤트인지 알려주는 번호
            "cctv_source_id": detection.cctv_source_id,

            # 어떤 날씨 기록과 연결된 이벤트인지 알려주는 번호
            "weather_log_id": detection.weather_log_id,

            # 이벤트 제목
            "event_title": detection.event_title,

            # 이벤트가 발생한 위치 이름
            "location_name": detection.location_name,

            # 위도
            "latitude": float(detection.latitude) if detection.latitude is not None else None,

            # 경도
            "longitude": float(detection.longitude) if detection.longitude is not None else None,

            # 날씨 종류
            "weather_type": detection.weather_type,

            # 일반 차량 개수
            "normal_vehicle_count": detection.normal_vehicle_count,

            # 위험 차량 개수
            "risk_vehicle_count": detection.risk_vehicle_count,

            # 전체 차량 개수
            "total_vehicle_count": detection.total_vehicle_count,

            # 교통 밀도 점수
            "traffic_density_score": detection.traffic_density_score,

            # 주요 차량 종류
            "main_vehicle_type": detection.main_vehicle_type,

            # 위험도 점수
            "risk_score": detection.risk_score,

            # 위험도 단계
            "risk_level": detection.risk_level,

            # 이벤트 상태
            "event_status": detection.event_status,

            # LLM이 만든 제목
            "llm_title": detection.llm_title,

            # LLM이 만든 요약
            "llm_summary": detection.llm_summary,

            # 관리자 메모
            "admin_memo": detection.admin_memo,

            # 낮/밤 정보
            "time_type": detection.time_type,

            # 탐지에 사용된 모델 이름
            "model_name": detection.model_name,

            # 탐지 신뢰도
            "detection_confidence": (
                float(detection.detection_confidence)
                if detection.detection_confidence is not None
                else None
            ),

            # 점수 필터 통과 여부
            "score_filter_passed": detection.score_filter_passed,

            # LLM 판단 결과
            "llm_decision": detection.llm_decision,

            # LLM 판단 이유
            "llm_reason": detection.llm_reason,

            # 알림 필요 여부
            "alert_required": detection.alert_required,

            # 오탐 의심 여부
            "false_positive_suspected": detection.false_positive_suspected,

            # 탐지 시간
            "detected_at": detection.detected_at.isoformat() if detection.detected_at else None,

            # 생성 시간
            "created_at": detection.created_at.isoformat() if detection.created_at else None,

            # 수정 시간
            "updated_at": detection.updated_at.isoformat() if detection.updated_at else None
        }