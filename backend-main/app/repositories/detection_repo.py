# SQLAlchemy에서 or_를 가져와.
# or_는 "이 조건 또는 저 조건"으로 검색할 때 쓰는 도구야.
# 예: 제목에 검색어가 있거나, 위치 이름에 검색어가 있거나 둘 중 하나면 찾기
from sqlalchemy import or_
from app import db

# DetectionEvent 모델을 가져와.
# 이 모델은 Supabase DB의 detection_events 테이블과 연결돼.
from ..models.detection_event import DetectionEvent


class DetectionRepository:

    # 이 클래스는 DB에서 탐지 이벤트를 찾아오는 역할을 해.
    # 쉽게 말하면 "DB야, 조건에 맞는 탐지 결과 찾아줘!"라고 말하는 곳이야.

    def find_all(
        self,
        page=1,
        per_page=10,
        keyword=None,
        start_date=None,
        end_date=None,
        location_name=None,
        weather_type=None,
        risk_level=None,
        main_vehicle_type=None,
        event_status=None,
        time_type=None,
        alert_required=None
    ):
        # detection_events 테이블에서 데이터를 찾기 시작해.
        # 아직 조건을 붙이지 않았기 때문에 전체 탐지 이벤트를 대상으로 해.
        query = DetectionEvent.query

        # keyword가 있으면 여러 글자 칸에서 한 번에 검색해.
        # 예: keyword가 "강남"이면 제목, 위치, LLM 제목, LLM 요약에서 "강남"을 찾아.
        if keyword:
            # %는 앞뒤에 다른 글자가 있어도 찾겠다는 뜻이야.
            # 예: "%강남%"은 "서울 강남대로"도 찾을 수 있어.
            search = f"%{keyword}%"

            # event_title, location_name, llm_title, llm_summary 중 하나라도
            # 검색어가 들어가면 결과에 포함해.
            query = query.filter(
                or_(
                    # 이벤트 제목에서 검색어를 찾아.
                    DetectionEvent.event_title.ilike(search),

                    # 위치 이름에서 검색어를 찾아.
                    DetectionEvent.location_name.ilike(search),

                    # LLM이 만든 제목에서 검색어를 찾아.
                    DetectionEvent.llm_title.ilike(search),

                    # LLM이 만든 요약에서 검색어를 찾아.
                    DetectionEvent.llm_summary.ilike(search)
                )
            )

        # start_date가 있으면 그 날짜 이후의 탐지 결과만 찾아.
        # 예: start_date=2026-05-01 이면 5월 1일 이후 데이터만 찾기
        if start_date:
            query = query.filter(DetectionEvent.detected_at >= start_date)

        # end_date가 있으면 그 날짜 이전의 탐지 결과만 찾아.
        # 예: end_date=2026-05-18 이면 5월 18일 이전 데이터만 찾기
        if end_date:
            query = query.filter(DetectionEvent.detected_at <= end_date)

        # location_name이 있으면 해당 위치 이름만 찾아.
        # 예: location_name=강남대로
        if location_name:
            query = query.filter(
                DetectionEvent.location_name.ilike(f"%{location_name}%")
            )

        # weather_type이 있으면 해당 날씨만 찾아.
        # 예: weather_type=rain 이면 비 오는 상황만 찾기
        if weather_type:
            query = query.filter(DetectionEvent.weather_type == weather_type)

        # risk_level이 있으면 해당 위험도만 찾아.
        # 예: risk_level=high 이면 위험도 high만 찾기
        if risk_level:
            query = query.filter(DetectionEvent.risk_level == risk_level)

        # main_vehicle_type이 있으면 해당 주요 차량 종류만 찾아.
        # 예: main_vehicle_type=heavy_truck 이면 대형 트럭 관련 이벤트만 찾기
        if main_vehicle_type:
            query = query.filter(DetectionEvent.main_vehicle_type == main_vehicle_type)

        # event_status가 있으면 해당 상태만 찾아.
        # 예: event_status=pending 이면 아직 처리 중인 이벤트만 찾기
        if event_status:
            query = query.filter(DetectionEvent.event_status == event_status)

        # time_type이 있으면 낮/밤 조건으로 찾아.
        # 예: time_type=night 이면 야간 탐지 결과만 찾기
        if time_type:
            query = query.filter(DetectionEvent.time_type == time_type)

        # alert_required 값이 있으면 알림 필요 여부로 찾아.
        # True면 알림이 필요한 이벤트만 찾고,
        # False면 알림이 필요 없는 이벤트만 찾아.
        if alert_required is not None:
            query = query.filter(DetectionEvent.alert_required == alert_required)

        # detected_at 기준으로 최신 탐지 결과부터 정렬해.
        # paginate는 데이터를 페이지 단위로 나눠서 가져오는 기능이야.
        # 예: 1페이지에 10개씩 보여주기
        return query.order_by(DetectionEvent.detected_at.desc()).paginate(
            page=page,              # 몇 번째 페이지인지 정해.
            per_page=per_page,      # 한 페이지에 몇 개 보여줄지 정해.
            error_out=False         # 없는 페이지여도 에러 대신 빈 결과를 줘.
        )

    def find_by_id(self, detection_id):
    # detection_id는 탐지 이벤트의 고유 번호야.
    # 예: /api/detections/1 이면 detection_id는 1이 돼.

        # DetectionEvent 테이블에서 id가 detection_id와 같은 데이터 1개를 찾아.
        # first()는 조건에 맞는 데이터 중 첫 번째 1개만 가져오는 기능이야.
        return DetectionEvent.query.filter(
            DetectionEvent.id == detection_id
        ).first()
    
    def create_detection_event(self, data: dict):
        # 탐지 이벤트를 DB에 새로 저장해.
        event = DetectionEvent(**data)

        from app import db
        db.session.add(event)
        db.session.flush()

        return event

        