"""
Agent Planner

사용자 요청을 분석하고 실행 계획을 수립합니다.
"""

import json
from typing import Dict, Any, Optional, List
from enum import Enum

from src.utils.logger import setup_logger
from src.utils.openai_client import get_openai_client
from src.prompts import (
    get_system_prompt,
    get_intent_prompt,
    get_task_type_prompt,
    get_tool_selection_prompt
)

logger = setup_logger("agent_planner")


class TaskType(Enum):
    """작업 타입"""
    SIMPLE_QUERY = "simple_query"
    TOOL_REQUIRED = "tool_required"
    WEB_SEARCH = "web_search"
    MEMORY_QUERY = "memory_query"
    COMPLEX_CHAIN = "complex_chain"


class ExecutionPlan:
    """실행 계획"""
    
    def __init__(
        self,
        task_type: TaskType,
        intent: str,
        steps: List[Dict[str, Any]],
        requires_tools: List[str] = None,
        estimated_steps: int = 1
    ):
        self.task_type = task_type
        self.intent = intent
        self.steps = steps
        self.requires_tools = requires_tools or []
        self.estimated_steps = estimated_steps
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "task_type": self.task_type.value,
            "intent": self.intent,
            "steps": self.steps,
            "requires_tools": self.requires_tools,
            "estimated_steps": self.estimated_steps
        }


class AgentPlanner:
    """에이전트 계획 수립 클래스"""
    
    def __init__(self):
        """초기화"""
        self.openai_client = get_openai_client()
        logger.info("Agent Planner 초기화 완료")
    
    def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """
        사용자 의도 분석
        
        Args:
            user_input: 사용자 입력
        
        Returns:
            의도 분석 결과
            {
                "intent": str,
                "entities": dict,
                "confidence": float
            }
        """
        logger.info(f"의도 분석 시작: {user_input[:50]}...")
        
        try:
            prompt = get_intent_prompt(user_input)
            result = self.openai_client.query_with_json(
                system_prompt=get_system_prompt(),
                user_message=prompt
            )
            
            if result:
                logger.info(f"의도 분석 완료: {result.get('intent', 'unknown')}")
                return result
            else:
                logger.warning("의도 분석 실패, 기본값 반환")
                return {
                    "intent": "general_query",
                    "entities": {},
                    "confidence": 0.5
                }
        
        except Exception as e:
            logger.error(f"의도 분석 오류: {e}")
            return {
                "intent": "error",
                "entities": {},
                "confidence": 0.0
            }
    
    def determine_task_type(self, user_input: str) -> Dict[str, Any]:
        """
        작업 타입 결정
        
        Args:
            user_input: 사용자 입력
        
        Returns:
            작업 타입 분석 결과
            {
                "task_type": str,
                "reasoning": str,
                "requires_tools": list,
                "estimated_steps": int
            }
        """
        logger.info("작업 타입 결정 시작")
        
        try:
            prompt = get_task_type_prompt(user_input)
            result = self.openai_client.query_with_json(
                system_prompt=get_system_prompt(),
                user_message=prompt
            )
            
            if result:
                task_type = result.get("task_type", "simple_query")
                logger.info(f"작업 타입 결정: {task_type}")
                return result
            else:
                logger.warning("작업 타입 결정 실패, 기본값 반환")
                return {
                    "task_type": "simple_query",
                    "reasoning": "분석 실패",
                    "requires_tools": [],
                    "estimated_steps": 1
                }
        
        except Exception as e:
            logger.error(f"작업 타입 결정 오류: {e}")
            return {
                "task_type": "simple_query",
                "reasoning": f"오류 발생: {e}",
                "requires_tools": [],
                "estimated_steps": 1
            }
    
    def select_tools(
        self,
        task_description: str,
        available_mcp_tools: List[str] = None
    ) -> Dict[str, Any]:
        """
        도구 선택
        
        Args:
            task_description: 작업 설명
            available_mcp_tools: 사용 가능한 MCP 도구 목록
        
        Returns:
            도구 선택 결과
            {
                "selected_tool": str,
                "tool_name": str,
                "reasoning": str,
                "params": dict
            }
        """
        logger.info("도구 선택 시작")
        
        if available_mcp_tools is None:
            available_mcp_tools = []
        
        try:
            prompt = get_tool_selection_prompt(task_description, available_mcp_tools)
            result = self.openai_client.query_with_json(
                system_prompt=get_system_prompt(),
                user_message=prompt
            )
            
            if result:
                selected = result.get("selected_tool", "llm")
                logger.info(f"도구 선택 완료: {selected}")
                return result
            else:
                logger.warning("도구 선택 실패, LLM 사용")
                return {
                    "selected_tool": "llm",
                    "tool_name": "",
                    "reasoning": "분석 실패, LLM 사용",
                    "params": {}
                }
        
        except Exception as e:
            logger.error(f"도구 선택 오류: {e}")
            return {
                "selected_tool": "llm",
                "tool_name": "",
                "reasoning": f"오류 발생: {e}",
                "params": {}
            }
    
    
    def decompose_complex_task(self, user_input: str) -> List[Dict[str, Any]]:
        """
        복잡한 작업을 여러 단계로 분해
        
        Args:
            user_input: 사용자 입력
        
        Returns:
            단계 리스트
        """
        logger.info("복잡한 작업 분해 시작")
        
        from src.prompts import get_task_decomposition_prompt
        
        prompt = get_task_decomposition_prompt(user_input)
        
        try:
            result = self.openai_client.query_with_json(
                system_prompt=get_system_prompt(),
                user_message=prompt
            )
            
            if result and "steps" in result:
                steps = result["steps"]
                logger.info(f"작업 분해 완료: {len(steps)}단계")
                return steps
            else:
                logger.warning("작업 분해 실패, 단일 LLM 단계로 fallback")
                return [{
                    "step_number": 1,
                    "action": "llm_response",
                    "tool": "llm",
                    "description": "복합 작업 처리",
                    "reasoning": "작업 분해 실패"
                }]
                
        except Exception as e:
            logger.error(f"작업 분해 오류: {e}")
            return [{
                "step_number": 1,
                "action": "llm_response",
                "tool": "llm",
                "description": "복합 작업 처리",
                "reasoning": "분해 오류로 인한 fallback"
            }]
    
    def create_execution_plan(
        self,
        user_input: str,
        available_mcp_tools: List[str] = None
    ) -> ExecutionPlan:
        """
        실행 계획 생성
        
        Args:
            user_input: 사용자 입력
            available_mcp_tools: 사용 가능한 MCP 도구 목록
        
        Returns:
            ExecutionPlan 객체
        """
        logger.info("실행 계획 생성 시작")
        
        # 1. 의도 분석
        intent_result = self.analyze_intent(user_input)
        
        # 2. 작업 타입 결정
        task_type_result = self.determine_task_type(user_input)
        task_type_str = task_type_result.get("task_type", "simple_query")
        
        try:
            task_type = TaskType(task_type_str)
        except ValueError:
            logger.warning(f"알 수 없는 작업 타입: {task_type_str}, simple_query 사용")
            task_type = TaskType.SIMPLE_QUERY
        
        # 3. 실행 단계 생성
        steps = []
        
        if task_type == TaskType.SIMPLE_QUERY:
            # 단순 질문: LLM만 사용
            steps.append({
                "step": 1,
                "action": "llm_response",
                "tool": "llm",
                "description": "LLM을 사용하여 직접 응답"
            })
        
        elif task_type == TaskType.TOOL_REQUIRED:
            # 도구 필요: 도구 선택 후 실행
            tool_selection = self.select_tools(user_input, available_mcp_tools)
            steps.append({
                "step": 1,
                "action": "tool_call",
                "tool": tool_selection.get("selected_tool", "llm"),
                "tool_name": tool_selection.get("tool_name", ""),
                "params": tool_selection.get("params", {}),
                "description": tool_selection.get("reasoning", "")
            })
        
        elif task_type == TaskType.WEB_SEARCH:
            # 웹 검색
            steps.append({
                "step": 1,
                "action": "web_search",
                "tool": "web_search",
                "description": "웹 검색을 통한 정보 수집"
            })
        
        elif task_type == TaskType.MEMORY_QUERY:
            # 메모리 조회
            steps.append({
                "step": 1,
                "action": "memory_query",
                "tool": "memory",
                "description": "장기 메모리 조회"
            })
        
        else:
            # 복합 작업: LLM을 사용하여 작업 분해
            decomposed_steps = self.decompose_complex_task(user_input)
            
            for idx, decomposed_step in enumerate(decomposed_steps, 1):
                steps.append({
                    "step": idx,
                    "action": decomposed_step.get("action", "llm_response"),
                    "tool": decomposed_step.get("tool", "llm"),
                    "description": decomposed_step.get("description", ""),
                    "reasoning": decomposed_step.get("reasoning", "")
                })
        
        plan = ExecutionPlan(
            task_type=task_type,
            intent=intent_result.get("intent", "unknown"),
            steps=steps,
            requires_tools=task_type_result.get("requires_tools", []),
            estimated_steps=task_type_result.get("estimated_steps", len(steps))
        )
        
        logger.info(f"실행 계획 생성 완료: {task_type.value}, {len(steps)}단계")
        
        return plan
