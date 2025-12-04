"""
Result Synthesizer

실행 결과를 통합하여 최종 응답을 생성합니다.
"""

from typing import Dict, Any, List, Optional
from src.utils.logger import setup_logger
from src.utils.openai_client import get_openai_client
from src.prompts.templates import get_result_synthesis_prompt

logger = setup_logger("result_synthesizer")


class ResultSynthesizer:
    """결과 통합 클래스"""
    
    def __init__(self):
        """초기화"""
        self.openai_client = get_openai_client()
        logger.info("Result Synthesizer 초기화 완료")
    
    def synthesize(
        self,
        user_input: str,
        execution_result: Dict[str, Any]
    ) -> str:
        """
        결과 통합 및 응답 생성
        
        Args:
            user_input: 사용자 입력
            execution_result: 실행 결과 딕셔너리
        
        Returns:
            최종 응답 문자열
        """
        logger.info("결과 통합 시작")
        
        status = execution_result.get("status")
        steps = execution_result.get("steps", [])
        final_output = execution_result.get("final_output")
        error = execution_result.get("error")
        
        # 1. 단일 스텝이고 LLM 응답인 경우 그대로 반환
        if len(steps) == 1 and steps[0]["tool_used"] == "llm" and status == "completed":
            logger.info("단일 LLM 응답 반환")
            return str(final_output)
        
        # 2. 오류 발생 시
        if status == "failed":
            logger.warning("실행 실패, 오류 메시지 생성")
            return self._generate_error_response(user_input, error, steps)
        
        # 3. 복합 결과 통합
        try:
            # 실행 단계 요약
            step_summaries = []
            for step in steps:
                step_num = step.get("step_number")
                tool = step.get("tool_used")
                output = str(step.get("output"))[:500]  # 너무 긴 출력은 자름
                step_summaries.append(f"Step {step_num} ({tool}): {output}")
            
            prompt = get_result_synthesis_prompt(user_input, step_summaries)
            
            response = self.openai_client.simple_query(
                system_prompt="당신은 실행 결과를 종합하여 사용자에게 명확하게 전달하는 AI 어시스턴트입니다.",
                user_message=prompt
            )
            
            logger.info("결과 통합 완료")
            return response
            
        except Exception as e:
            logger.error(f"결과 통합 오류: {e}")
            # fallback: 마지막 결과 반환
            return str(final_output) if final_output else "죄송합니다. 결과를 처리하는 중에 오류가 발생했습니다."
    
    def _generate_error_response(
        self,
        user_input: str,
        error: str,
        steps: List[Dict[str, Any]]
    ) -> str:
        """오류 응답 생성"""
        executed_steps = len(steps)
        
        msg = f"죄송합니다. 요청을 처리하는 중에 문제가 발생했습니다.\n\n"
        msg += f"오류 내용: {error}\n"
        
        if executed_steps > 0:
            msg += f"\n{executed_steps}단계까지 진행되었으나 중단되었습니다."
            
        return msg
