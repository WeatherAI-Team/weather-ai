# 🚀 TNGeneration Project

>본 프로젝트는 **Next.js**, **Flask**, **FastAPI**를 이용한 서비스 모델 생성 및 관리 시스템입니다.

---

## 🏗️ Project Architecture (Folder Structure)

```
/TNGeneration-Project (Root)
│
├── /frontend                 # [Next.js] 사용자 UI 및 클라이언트 서버
│   ├── /src
│   │   ├── /app              # app Router (메인, 게시판, 로그인 등)
│   │   ├── /components       # 재사용 UI 컴포넌트 (Header, Footer, Card 등)
│   │   │   └── /common       # 버튼, 입력창 등 공통 부품
│   │   ├── /services         # API 통신 로직 (Axios/Fetch 설정)
│   │   ├── /hooks            # 공통 비즈니스 로직 (Custom Hooks)
│   │   └── /styles           # 전역 CSS 및 테마 설정
│   ├── .env.local            # [분리] 프론트 전용 환경변수
│   ├── next.config.js
│   └── package.json
│
├── /backend-main
│   ├── /app
│   │   ├── __init__.py      # 앱 생성 및 Blueprint/CORS/DB 등록
│   │   ├── /api              # [Controller] 요청/응답 처리 (Blueprint)
│   │   │     ├── member_api.py
│   │   │     └── board_api.py
│   │   ├── /services         # [Service] 비즈니스 로직 (AI 서버 통신 등)
│   │   │     ├── member_service.py
│   │   │     └── board_service.py
│   │   ├── /repositories     # [Repository] DB 접근 로직 (SQLAlchemy 쿼리)
│   │   │     ├── user_repo.py
│   │   │     └── post_repo.py
│   │   ├── /models           # [Model] DB 테이블 정의 (User, Post)
│   │   ├── /schemas          # [Schema] 데이터 검증 및 직렬화 (Marshmallow 등)
│   │   └── /utils            # [Utils] 공통 함수, AI 서버 호출 모듈 등
│   ├── .env                  # # [분리] 메인 백엔드 전용 환경변수 (DB 등)
│   ├── config.py
│   ├── requirements.txt
│   └── run.py
│ 
├── /backend-ai               # [FastAPI] AI 모델 추론 전용 서버
│   ├── /app
│   │   ├── main.py           # FastAPI 실행 및 엔드포인트
│   │   ├── /models           # AI 모델 파일 (.pt, .h5 등) 및 로드 로직
│   │   └── /schemas          # 데이터 검증을 위한 Pydantic 모델
│   ├── .env                  # # [분리] AI 서버 전용 환경변수 (모델 경로 등)
│   └── requirements.txt
│
├── .gitignore                # Python, Node, .env 등 제외 설정
└── README.md                 # 프로젝트 문서 (아키텍처, 실행 방법)
```

## 🛠 각 작업별 기본 세팅
> 프로젝트를 처음 git clone 받은 후, 각 폴더에서 아래 설정을 완료해야 합니다.

### 1. 프론트엔드 세팅
```Bash
cd frontend
npm install
npm run dev
```

### 2. 메인 백엔드 세팅 (Flask)
```Bash
cd backend-main
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```
### 3. AI 백엔드 세팅 (FastAPI)
```Bash
cd backend-ai
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 🔄 작업 흐름 및 협업 규칙
### 💡 터미널 멀티태스킹 권장 (강추 ⭐)
환경변수 충돌 방지를 위해 VSCode 터미널 탭을 3개 열어서 사용하는 것을 권장합니다.
```
Tab 1: frontend 전용

Tab 2: backend-main (Flask) 전용

Tab 3: backend-ai (FastAPI) 전용
```
### 🤝 협업 규칙 (Git Convention)
```
Branch 전략: main 브랜치에 직접 Push 금지! 기능별 브랜치 생성 후 PR(Pull Request)을 날려주세요.

환경 변수: .env 파일은 보안상 공유되지 않습니다. 필요한 설정값은 **노션(Notion)**을 참고하세요.

패키지 관리: 새로운 라이브러리를 설치했다면 반드시 아래 명령어를 실행해 주세요.

pip freeze > requirements.txt
```
## 📝 참고사항 (Notes)
AI 모델 경로: YOLO 모델 파일(.pt)은 대용량이므로 따로 공유합니다. backend-ai/app/models/ 폴더에 수동으로 넣어주세요.

API 문서 확인 (Swagger): AI 서버 실행 후 http://localhost:8000/docs에 접속하면 자동 생성된 API 명세서를 확인할 수 있습니다.


---

### **💡 추가로 신경 쓰면 좋은 점**
1.  **포트 번호 강조:** 프론트(3000), 메인(5000), AI(8000) 포트가 서로 겹치지 않게 명시해두면 나중에 통신 오류를 잡기 훨씬 편합니다.
