# AI Agent Mini Assistant 🚀

개인 비서처럼 동작하는 AI Agent 시스템입니다.

## 📋 주요 기능

- **LLM 기반 대화**: OpenAI API를 사용한 자연어 처리
- **프롬프트 체이닝**: 복합 작업을 단계별로 처리
- **MCP 툴 통합**: Notion 등 외부 도구 연동
- **웹 검색**: 실시간 정보 검색 및 보강
- **메모리 시스템**: 대화 컨텍스트 및 사용자 선호도 저장

## 🛠️ 설치 방법

### 1. 필수 요구사항
- Python 3.12 이상
- uv (Python 패키지 관리자)

### 2. 프로젝트 설정

```bash
# 저장소 클론 (또는 디렉토리 이동)
cd miniviseo2

# 가상환경 생성
uv venv

# 가상환경 활성화
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 의존성 설치
uv pip install -e .
```

### 3. 환경변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 값을 설정합니다:

```bash
cp .env.example .env
```

`.env` 파일에 다음 값을 설정:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# MCP Server Configuration (JSON format)
# 예시: Notion MCP 서버 설정
MCP_SERVERS={"notion": {"url": "http://localhost:3000", "description": "Notion MCP Server"}}

# 여러 서버 설정 예시
# MCP_SERVERS={"notion": {"url": "http://localhost:3000", "description": "Notion MCP Server"}, "calendar": {"url": "http://localhost:3001", "description": "Calendar MCP Server"}}

LOG_LEVEL=INFO
MEMORY_FILE=data/memory.json
```

## 🚀 사용 방법

```bash
python app.py
```

CLI 인터페이스가 시작되며, 자연어로 요청을 입력할 수 있습니다.

### 예시

```
> 파이썬에서 리스트를 합치는 방법 알려줘
> "회의록" 페이지에 할 일 "AI 기능 추가"를 만들어줘
> 오늘 서울 날씨 어때?
> 내가 어제 기억해 달라고 한 프로젝트 이름이 뭐였지?
```

## 📁 프로젝트 구조

```
miniviseo2/
├── src/
│   ├── agent/          # 에이전트 핵심 로직
│   │   ├── planner.py  # 작업 계획 수립
│   │   ├── executor.py # 체인 실행
│   │   └── synthesizer.py # 결과 통합
│   ├── tools/          # 도구 통합
│   │   ├── mcp_client.py  # MCP 클라이언트
│   │   ├── web_search.py  # 웹 검색
│   │   └── router.py      # 도구 라우터
│   ├── memory/         # 메모리 관리
│   │   ├── session.py     # 세션 메모리
│   │   └── persistent.py  # 장기 메모리
│   ├── prompts/        # 프롬프트 템플릿
│   │   ├── system.py      # 시스템 프롬프트
│   │   └── templates.py   # 템플릿 관리
│   └── utils/          # 유틸리티
│       ├── logger.py      # 로깅
│       └── parser.py      # 입력 파싱
├── data/               # 데이터 저장소
│   └── memory.json     # 메모리 저장
├── logs/               # 로그 파일
├── app.py              # 메인 엔트리 포인트
└── pyproject.toml      # 프로젝트 설정
```

## 🏗️ 아키텍처

```
User
 ↓
Input Parser
 ↓
Agent Planner ───────────────→ Memory Manager
 ↓                                      ↑
Tool Router → MCP Tool Server           │
        │           ↓                   │
        │       Tool Result             │
        └→ Web Search Engine            │
 ↓                                      │
Chain Executor --------------------------
 ↓
Result Synthesizer
 ↓
User
```

## 📝 개발 상태

현재 프로젝트는 초기 설정 단계입니다. 자세한 개발 계획은 `prd.md`와 `tasklist.md`를 참고하세요.

## 📄 라이선스

이 프로젝트는 학습용 토이 프로젝트입니다.
