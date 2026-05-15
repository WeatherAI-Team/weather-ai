# ⛅ Weather-Ai

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
│   │   │     ├── member_repo.py
│   │   │     └── post_repo.py
│   │   ├── /models           # [Model] DB 테이블 정의 (Member, Post)
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

<br>

## 🛠 각 작업별 기본 세팅
> 프로젝트를 처음 git clone 받은 후, 각 폴더에서 아래 설정을 완료해야 합니다.

### 0. 프론트엔드 최초 1회 세팅
```Bash
# 1. 클론
git clone https://github.com/WeatherAI-Team/weather-ai.git

# 2. nvm 설치 (nvm이 없는 경우에만)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# 설치 후 터미널 재시작 필요

# 3. Node 20 설치 및 설정
nvm install 20
nvm use 20
nvm alias default 20
```

### 1. 프론트엔드 세팅 (Next.js)
```Bash
cd frontend
npm install
npm run dev
```

### 2. 메인 백엔드 세팅 (Flask)
```Bash
cd backend-main
python3 -m venv .venv
source .venv/bin/activate  
pip install -r requirements.txt
python run.py
```
### 3. AI 백엔드 세팅 (FastAPI)
```Bash
cd backend-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

<br>

## 🔄 작업 흐름 및 협업 규칙
### 💡 터미널 멀티태스킹 권장 (강추 ⭐)
환경변수 충돌 방지를 위해 VSCode 터미널 탭을 3개 열어서 사용하는 것을 권장합니다.
```
Tab 1: frontend 전용

Tab 2: backend-main (Flask) 전용

Tab 3: backend-ai (FastAPI) 전용
```

<br>

### 🤝 협업 규칙 (Git Convention)
```
⭐⭐⭐ 작업 시작 전 git pull origin main 으로 최신화 ⭐⭐⭐

환경 변수: .env 파일은 보안상 공유되지 않습니다. 필요한 설정값은 **노션(Notion)**을 참고하세요.

패키지 관리: 새로운 라이브러리를 설치했다면 반드시 아래 명령어를 실행해 주세요.

프론트엔드
⭐⭐npm install <패키지명> (자동으로 package.json에 기록됨)⭐⭐

백엔드
⭐⭐pip freeze > requirements.txt⭐⭐

Branch 전략: main 브랜치에 직접 Push 금지! 기능별 또는 작업자별 브랜치 생성 후 PR(Pull Request)을 날려주세요.
```

<br>
<br>

## 🚀 작업 순서 및 깃허브 푸쉬 방법
```bash
## 🚀 작업 시작 전 (필수!)
1. git checkout main : 메인 브랜치로 이동
2. git pull origin main : 최신 코드 가져오기
3. git checkout -b "브랜치명" 또는 개인브랜치가 존재하면 git checkout "브랜치명"

## 🛠 작업 완료 후 (푸쉬 방법)
1. git add . : 변경된 모든 파일 담기
2. git commit -m "깃컨밴션 : 작업 내용" : 깃컨벤션 지켜서 커밋 (아래 리스트 참고)
예시 : git commit -m "feat: CCTV 조회 API 구현 및 서비스 로직 추가"
3. git push origin "브랜치명" : 내 브랜치에 코드 올리기

※ 주의: 새로운 라이브러리 설치 시 반드시 `pip freeze` 확인!
```

<br>


## 📜 깃컨벤션
```bash
Feat : 새로운 기능 추가
Fix : 버그 수정
Docs : 문서 수정
Style : 코드 포맷팅, 세미콜론 누락, 코드 변경이 없는 경우
Refactor : 코드 리펙토링
Test : 테스트(테스트 코드 추가, 수정, 삭제, 비즈니스 로직에 변경이 없는 경우)
Chore : 위에 걸리지 않는 기타 변경사항 (빌드 스크립트 수정, assets image, 패키지 매니저 등)
Design : CSS 등 사용자 UI 디자인 변경
Comment : 필요한 주석 추가 및 변경
Init : 프로젝트 초기 생성
Rename : 파일 혹은 폴더명 수정하거나 옮기는 경우
Remove : 파일을 삭제하는 작업만 수행하는 경우
```


<br>
<br>

# ⚠️ PR(Pull Request) 생성 규칙
1. 깃허브 사이트에서 **base: dev** ← **compare: 내-브랜치** 방향으로 PR을 날려주세요.
   (※ main이 아니라 **dev** 브랜치로 날려야 합니다!)
2. 관리자가 코드 검수 및 로컬 테스트 후 병합을 승인합니다.

<br>

## 📝 참고사항 (Notes)
AI 모델 경로: YOLO 모델 파일(.pt)은 대용량이므로 따로 공유합니다. 폴더에 수동으로 넣어주세요.

API 문서 확인 (Swagger): AI 서버 실행 후 http://localhost:8000/docs에 접속하면 자동 생성된 API 명세서를 확인할 수 있습니다.
