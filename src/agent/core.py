"""
AI Agent Core Logic

에이전트의 핵심 로직을 담고 있는 클래스입니다.
CLI와 Web API에서 공통으로 사용됩니다.
"""

import traceback
from src.utils.logger import setup_logger
from src.agent import AgentPlanner, ChainExecutor, ResultSynthesizer
from src.memory import SessionMemory, PersistentMemory

logger = setup_logger("agent_core")


class AIAgent:
    """AI Agent 메인 클래스"""
    
    def __init__(self):
        """초기화"""
        logger.info("AI Agent 초기화 시작")
        
        # 컴포넌트 초기화
        self.planner = AgentPlanner()
        self.executor = ChainExecutor()
        self.synthesizer = ResultSynthesizer()
        self.session_memory = SessionMemory()
        self.persistent_memory = PersistentMemory()
        
        logger.info("AI Agent 초기화 완료")
    
    def process_request(self, user_input: str) -> str:
        """
        사용자 요청 처리
        
        Args:
            user_input: 사용자 입력
        
        Returns:
            최종 응답
        """
        logger.info(f"요청 처리 시작: {user_input[:50]}...")
        
        try:
            # 0. 세션 메모리에 사용자 입력 저장
            self.session_memory.add_message("user", user_input)
            
            # 1. 장기 메모리 자동 저장 분석
            saved_memory = self.persistent_memory.analyze_and_remember(user_input)
            if saved_memory:
                logger.info(f"중요 정보 저장됨: {saved_memory}")
            
            # 2. 실행 계획 수립
            # TODO: 세션 컨텍스트와 장기 메모리를 프롬프트에 포함해야 함
            plan = self.planner.create_execution_plan(user_input)
            
            # 3. 체인 실행
            execution_result = self.executor.execute_chain(plan, user_input)
            
            # 4. 결과 통합 및 응답 생성
            final_response = self.synthesizer.synthesize(user_input, execution_result)
            
            # 5. 세션 메모리에 응답 저장
            self.session_memory.add_message("assistant", final_response)
            
            return final_response
            
        except Exception as e:
            logger.error(f"요청 처리 중 오류 발생: {e}")
            traceback.print_exc()
            return "죄송합니다. 시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
