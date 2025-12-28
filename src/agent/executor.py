"""
Chain Executor

실행 계획을 단계별로 실행합니다.
"""

from typing import Dict, Any, Optional, List
from enum import Enum

from src.utils.logger import setup_logger, log_chain_step
from src.utils.openai_client import get_openai_client
from src.prompts import get_system_prompt, get_tool_selection_prompt, get_mcp_tool_param_prompt
from src.agent.planner import ExecutionPlan, TaskType

logger = setup_logger("chain_executor")


class ExecutionStatus(Enum):
    """실행 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    FALLBACK = "fallback"


class StepResult:
    """단계 실행 결과"""
    
    def __init__(
        self,
        step_number: int,
        status: ExecutionStatus,
        output: Any = None,
        error: Optional[str] = None,
        tool_used: Optional[str] = None
    ):
        self.step_number = step_number
        self.status = status
        self.output = output
        self.error = error
        self.tool_used = tool_used
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "step_number": self.step_number,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "tool_used": self.tool_used
        }


class ChainExecutor:
    """체인 실행 엔진"""
    
    def __init__(self):
        """초기화"""
        self.openai_client = get_openai_client()
        self.execution_history: List[StepResult] = []
        
        # 도구 및 메모리 모듈 초기화
        # 순환 참조 방지를 위해 내부 import 또는 지연 초기화 고려
        from src.tools.router import ToolRouter
        from src.memory.persistent import PersistentMemory
        
        self.tool_router = ToolRouter()
        self.persistent_memory = PersistentMemory()
        
        logger.info("Chain Executor 초기화 완료")
    
    def execute_step(
        self,
        step: Dict[str, Any],
        user_input: str,
        context: Dict[str, Any] = None
    ) -> StepResult:
        """
        단일 스텝 실행
        
        Args:
            step: 실행할 단계 정보
            user_input: 사용자 입력
            context: 실행 컨텍스트 (이전 단계 결과 등)
        
        Returns:
            StepResult 객체
        """
        step_number = step.get("step", 1)
        action = step.get("action", "")
        tool = step.get("tool", "llm")
        
        log_chain_step(logger, step_number, action, {"tool": tool})
        
        try:
            if tool == "llm":
                # LLM 직접 응답
                result = self._execute_llm_step(user_input, context)
                return StepResult(
                    step_number=step_number,
                    status=ExecutionStatus.COMPLETED,
                    output=result,
                    tool_used="llm"
                )
            
            elif tool == "mcp":
                # MCP 도구 호출
                result = self._execute_mcp_step(step, user_input, context)
                return StepResult(
                    step_number=step_number,
                    status=ExecutionStatus.COMPLETED,
                    output=result,
                    tool_used="mcp"
                )
            
            elif tool == "web_search":
                # 웹 검색
                result = self._execute_web_search_step(user_input, context)
                return StepResult(
                    step_number=step_number,
                    status=ExecutionStatus.COMPLETED,
                    output=result,
                    tool_used="web_search"
                )
            
            elif tool == "memory":
                # 메모리 조회
                result = self._execute_memory_step(user_input, context)
                return StepResult(
                    step_number=step_number,
                    status=ExecutionStatus.COMPLETED,
                    output=result,
                    tool_used="memory"
                )
            
            else:
                # 알 수 없는 도구
                logger.warning(f"알 수 없는 도구: {tool}, LLM 사용")
                result = self._execute_llm_step(user_input, context)
                return StepResult(
                    step_number=step_number,
                    status=ExecutionStatus.COMPLETED,
                    output=result,
                    tool_used="llm"
                )
        
        except Exception as e:
            logger.error(f"스텝 실행 오류: {e}")
            return StepResult(
                step_number=step_number,
                status=ExecutionStatus.FAILED,
                error=str(e),
                tool_used=tool
            )
    
    def _execute_llm_step(
        self,
        user_input: str,
        context: Dict[str, Any] = None
    ) -> str:
        """LLM 스텝 실행"""
        logger.info("LLM 스텝 실행")
        
        system_prompt = get_system_prompt()
        
        # 컨텍스트가 있으면 추가
        user_message = ""
        
        if context and context.get("conversation_history"):
            user_message += f"[이전 대화 맥락]:\n{context['conversation_history']}\n\n"

        if context and context.get("previous_results"):
             user_message += f"이전 단계 결과:\n{context['previous_results']}\n\n"
             
        user_message += f"사용자 요청: {user_input}"
        
        response = self.openai_client.simple_query(system_prompt, user_message)
        return response
    
    def _execute_mcp_step(
        self,
        step: Dict[str, Any],
        user_input: str,
        context: Dict[str, Any] = None
    ) -> str:
        """MCP 스텝 실행"""
        logger.info("MCP 스텝 실행")
        
        tool_name = step.get("tool_name", "")
        params = step.get("params", {})
        
        # 도구 이름이 없거나 유효하지 않은 경우 JIT(Just-In-Time) 도구 선택 수행
        if not tool_name or tool_name.strip() == "":
            logger.warning("MCP 도구 이름 누락, JIT 도구 선택 시작")
            
            # 1. 사용 가능한 도구 목록 조회
            available_mcp_tools = []
            mcp_client = self.tool_router.mcp_client
            for server_name in mcp_client.list_servers():
                tools = mcp_client.get_available_tools(server_name)
                available_mcp_tools.extend([f"{server_name}.{tool}" for tool in tools])
            
            # 2. 도구 스키마 조회
            tools_schema = mcp_client.get_all_tools_schema()
            
            # 3. 컨텍스트를 포함한 작업 설명 생성
            task_desc = f"사용자 요청: {user_input}\n"
            if context and context.get("previous_results"):
                task_desc += f"\n이전 단계 결과 (참고하여 파라미터 생성):\n"
                for idx, res in enumerate(context["previous_results"]):
                    task_desc += f"[{idx+1}] {res}\n"
            
            step_desc = step.get("description", "")
            if step_desc:
                task_desc += f"\n현재 단계 목표: {step_desc}"
            
            # 4. LLM에게 도구 선택 요청
            prompt = get_tool_selection_prompt(task_desc, available_mcp_tools, tools_schema)
            selection_result = self.openai_client.query_with_json(
                system_prompt=get_system_prompt(),
                user_message=prompt
            )
            
            if selection_result:
                tool_name = selection_result.get("tool_name", "")
                params = selection_result.get("params", {})
                logger.info(f"JIT 도구 선택 완료: {tool_name}, 파라미터: {params}")
            else:
                logger.error("JIT 도구 선택 실패")
                raise Exception("MCP 도구 이름을 결정할 수 없습니다.")
        
        # 5. 문맥(Context) 기반 파라미터 재생성 (Contextual Parameter Injection)
        # 도구 이름이 확정되었고, 이전 단계의 결과(Context)가 있다면 파라미터를 더 정교하게 다듬습니다.
        elif context and (context.get("previous_results") or context.get("conversation_history")) and tool_name:
            logger.info(f"이전 단계 결과 존재, 파라미터 재생성 시도: {tool_name}")
            try:
                # 도구 정보 가져오기
                mcp_client = self.tool_router.mcp_client
                server_name = tool_name.split(".")[0]
                tool_short_name = tool_name.split(".")[1]
                
                # 스키마 및 설명 조회
                schema = mcp_client.get_tool_schema(server_name, tool_short_name)
                tool_description = schema.get("description", "") if schema else "설명 없음"
                
                # 파라미터 스키마 포맷팅 (설명 포함)
                schema_str = ""
                input_schema = schema.get("inputSchema", {}) if schema else {}
                if input_schema:
                    properties = input_schema.get("properties", {})
                    for prop_name, prop_info in properties.items():
                        prop_type = prop_info.get("type", "any")
                        prop_desc = prop_info.get("description", "설명 없음")
                        schema_str += f"- {prop_name} ({prop_type}): {prop_desc}\n"
                
                # 프롬프트 구성: 사용자 요청 + 이전 결과
                enhanced_input = f"사용자 원본 요청: {user_input}\n\n"
                
                if context.get("conversation_history"):
                    enhanced_input += f"[이전 대화 맥락 (중요 참고)]:\n{context['conversation_history']}\n\n"

                if context.get("previous_results"):
                    enhanced_input += f"[이전 단계 실행 결과 (반드시 반영할 것)]:\n"
                    for idx, res in enumerate(context["previous_results"]):
                        enhanced_input += f"[{idx+1}] {res}\n"
                
                # LLM 요청
                param_prompt = get_mcp_tool_param_prompt(tool_name, tool_description, schema_str, enhanced_input)
                new_params = self.openai_client.query_with_json(
                    system_prompt=get_system_prompt(),
                    user_message=param_prompt
                )
                
                if new_params:
                    logger.info(f"파라미터 재생성 완료: {new_params}")
                    params = new_params
                
            except Exception as e:
                logger.warning(f"파라미터 재생성 중 오류 (기존 파라미터 사용): {e}")

        # Tool Router를 통해 호출
        result = self.tool_router.route_tool_call("mcp", tool_name, params, user_input)
        
        if result is None:
            raise Exception(f"MCP 도구 호출 실패: {tool_name}")
            
        return str(result)
    
    def _execute_web_search_step(
        self,
        user_input: str,
        context: Dict[str, Any] = None
    ) -> str:
        """웹 검색 스텝 실행"""
        logger.info("웹 검색 스텝 실행")
        
        # Tool Router를 통해 호출
        # 파라미터가 없으면 빈 딕셔너리 전달 (Router가 쿼리 생성)
        result = self.tool_router.route_tool_call("web_search", "search", {}, user_input)
        
        return str(result)
    
    def _execute_memory_step(
        self,
        user_input: str,
        context: Dict[str, Any] = None
    ) -> str:
        """메모리 스텝 실행"""
        logger.info("메모리 스텝 실행")
        
        # 장기 메모리 전체 조회 (또는 검색 로직 추가 가능)
        memories = self.persistent_memory.get_memory_string()
        
        return f"장기 메모리 조회 결과:\n{memories}"
    
    def execute_chain(
        self,
        plan: ExecutionPlan,
        user_input: str,
        conversation_history: str = None
    ) -> Dict[str, Any]:
        """
        전체 체인 실행
        
        Args:
            plan: 실행 계획
            user_input: 사용자 입력
        
        Returns:
            실행 결과
            {
                "status": str,
                "final_output": str,
                "steps": list,
                "error": str (optional)
            }
        """
        logger.info(f"체인 실행 시작: {len(plan.steps)}단계")
        
        self.execution_history = []
        context = {
            "previous_results": [],
            "conversation_history": conversation_history
        }
        
        for step in plan.steps:
            result = self.execute_step(step, user_input, context)
            self.execution_history.append(result)
            
            if result.status == ExecutionStatus.FAILED:
                # 오류 발생 시 fallback 시도
                logger.warning(f"스텝 {result.step_number} 실패, fallback 시도")
                fallback_result = self._handle_fallback(step, user_input, context, result.error)
                
                if fallback_result:
                    self.execution_history.append(fallback_result)
                    context["previous_results"].append(fallback_result.output)
                else:
                    # Fallback도 실패
                    logger.error("Fallback 실패, 체인 중단")
                    return {
                        "status": "failed",
                        "final_output": None,
                        "steps": [r.to_dict() for r in self.execution_history],
                        "error": result.error
                    }
            else:
                # 성공한 결과를 컨텍스트에 추가
                context["previous_results"].append(result.output)
        
        # 최종 결과
        final_output = self.execution_history[-1].output if self.execution_history else None
        
        logger.info("체인 실행 완료")
        
        return {
            "status": "completed",
            "final_output": final_output,
            "steps": [r.to_dict() for r in self.execution_history],
            "error": None
        }
    
    def _handle_fallback(
        self,
        failed_step: Dict[str, Any],
        user_input: str,
        context: Dict[str, Any],
        error: str
    ) -> Optional[StepResult]:
        """
        Fallback 처리
        
        Args:
            failed_step: 실패한 단계
            user_input: 사용자 입력
            context: 실행 컨텍스트
            error: 오류 메시지
        
        Returns:
            Fallback 결과 또는 None
        """
        failed_tool = failed_step.get("tool", "unknown")
        
        logger.info(f"Fallback 처리: {failed_tool} → 대안 도구 선택")
        
        # Fallback 전략
        if failed_tool == "mcp":
            # MCP 실패 → 웹 검색 시도
            logger.info("MCP 실패, 웹 검색으로 fallback")
            try:
                result = self._execute_web_search_step(user_input, context)
                return StepResult(
                    step_number=failed_step.get("step", 0),
                    status=ExecutionStatus.FALLBACK,
                    output=result,
                    tool_used="web_search"
                )
            except Exception as e:
                logger.error(f"웹 검색 fallback 실패: {e}")
        
        if failed_tool in ["mcp", "web_search"]:
            # MCP/웹 검색 실패 → LLM으로 fallback
            logger.info(f"{failed_tool} 실패, LLM으로 fallback")
            try:
                result = self._execute_llm_step(user_input, context)
                return StepResult(
                    step_number=failed_step.get("step", 0),
                    status=ExecutionStatus.FALLBACK,
                    output=result,
                    tool_used="llm"
                )
            except Exception as e:
                logger.error(f"LLM fallback 실패: {e}")
        
        return None
    
    def get_execution_summary(self) -> str:
        """
        실행 요약 가져오기
        
        Returns:
            실행 요약 문자열
        """
        if not self.execution_history:
            return "실행 기록 없음"
        
        summary = []
        for result in self.execution_history:
            status_emoji = "✅" if result.status == ExecutionStatus.COMPLETED else "❌"
            summary.append(
                f"{status_emoji} Step {result.step_number}: {result.tool_used} "
                f"({result.status.value})"
            )
        
        return "\n".join(summary)
