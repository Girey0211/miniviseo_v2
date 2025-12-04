"""
AI Agent Web Server

FastAPI 기반의 웹 서버입니다.
정적 파일을 서빙하고 REST API를 제공합니다.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.agent.core import AIAgent
from src.utils.config import config
from src.utils.logger import setup_logger

# 로거 설정
logger = setup_logger("server")

# FastAPI 앱 초기화
app = FastAPI(title="AI Agent Mini Assistant", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 에이전트 인스턴스 (전역)
agent = None


class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    response: str


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    global agent
    logger.info("웹 서버 시작: 에이전트 초기화 중...")
    
    if not config.validate():
        logger.error("필수 환경변수가 설정되지 않았습니다.")
        # 실제 운영 환경에서는 여기서 종료하거나 에러를 발생시켜야 함
    
    try:
        agent = AIAgent()
        logger.info("에이전트 초기화 완료")
    except Exception as e:
        logger.error(f"에이전트 초기화 실패: {e}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """채팅 엔드포인트"""
    global agent
    
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        response = agent.process_request(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"요청 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 정적 파일 서빙 (항상 가장 마지막에 위치)
# 프로젝트 루트의 static 디렉토리 찾기
# 현재 파일: src/server.py -> 프로젝트 루트: ../
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(project_root, "static")

if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


def main():
    """서버 실행 함수"""
    import uvicorn
    # uvicorn.run에서 reload=True를 사용하려면 문자열로 전달해야 하지만,
    # 패키지 구조상 복잡할 수 있으므로 app 객체 직접 전달 (reload 불가)
    # 개발 시에는 uv run uvicorn src.server:app --reload 사용 권장
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
