"""
AI Agent Mini Assistant - Main Entry Point

개인 비서처럼 동작하는 AI Agent 시스템의 메인 애플리케이션입니다.
"""

import sys
import traceback
from src.utils.config import config
from src.utils.logger import setup_logger
from src.agent.core import AIAgent

# 로거 설정
logger = setup_logger("app")


def main():
    """메인 애플리케이션 함수"""
    print("🚀 AI Agent Mini Assistant")
    print("=" * 50)
    print("개인 비서 AI 에이전트를 시작합니다.")
    print("종료하려면 'exit' 또는 'quit'를 입력하세요.")
    print("=" * 50)
    print()
    
    # 설정 검증
    if not config.validate():
        print("⚠️  경고: 필수 환경변수가 설정되지 않았습니다.")
        print("   .env 파일을 확인해주세요.")
        return
    else:
        print(f"✅ 설정 로드 완료 (모델: {config.openai_model})")
        if config.has_mcp_servers():
            print(f"   - MCP 서버: {', '.join(config.mcp_servers.keys())}")
        print()
    
    # 에이전트 초기화
    try:
        agent = AIAgent()
        print("✅ 에이전트 준비 완료! 무엇을 도와드릴까요?")
        print()
    except Exception as e:
        print(f"❌ 에이전트 초기화 실패: {e}")
        return
    
    # 대화 루프
    while True:
        try:
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "종료"]:
                print("\n👋 AI Agent를 종료합니다. 안녕히 가세요!")
                break
            
            # 에이전트에게 요청 처리 위임
            print("\nThinking...", end="", flush=True)
            response = agent.process_request(user_input)
            
            # 줄바꿈 처리 및 응답 출력
            print(f"\r{' ' * 20}\r", end="")  # Thinking... 지우기
            print(f"🤖 Agent: {response}")
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 AI Agent를 종료합니다. 안녕히 가세요!")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            print()


if __name__ == "__main__":
    main()
