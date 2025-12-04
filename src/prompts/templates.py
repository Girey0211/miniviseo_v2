"""
Prompt Templates

작업별 프롬프트 템플릿을 정의합니다.
"""

# Intent Classification 프롬프트
INTENT_CLASSIFICATION_PROMPT = """사용자의 요청을 분석하여 의도를 파악하세요.

사용자 요청: {user_input}

다음 형식으로 응답하세요:
```json
{{
  "intent": "사용자의 주요 의도",
  "entities": {{
    "날짜": "추출된 날짜",
    "이름": "추출된 이름",
    "기타": "기타 엔티티"
  }},
  "confidence": 0.0-1.0
}}
```
"""

# Task Type 분류 프롬프트
TASK_TYPE_CLASSIFICATION_PROMPT = """사용자의 요청을 분석하여 작업 타입을 결정하세요.

사용자 요청: {user_input}

## 작업 타입
1. **simple_query**: 일반적인 질문 (예: "파이썬에서 리스트 합치는 방법")
2. **tool_required**: 외부 도구 필요 (예: "Notion에 할 일 추가")
3. **web_search**: 실시간 정보 필요 (예: "오늘 날씨")
4. **memory_query**: 메모리 조회 (예: "내가 기억해 달라고 한 것")
5. **complex_chain**: 여러 단계 필요 (예: "날씨 검색 후 Notion에 기록")

다음 형식으로 응답하세요:
```json
{{
  "task_type": "작업 타입",
  "reasoning": "이 타입을 선택한 이유",
  "requires_tools": ["필요한 도구 목록"],
  "estimated_steps": 1
}}
```
"""

# Tool Selection 프롬프트
TOOL_SELECTION_PROMPT = """주어진 작업에 가장 적합한 도구를 선택하세요.

작업: {task_description}
사용 가능한 MCP 도구: {available_mcp_tools}

## 도구 선택 기준
1. LLM 자체 지식으로 가능하면 도구 불필요
2. 외부 데이터/서비스 필요 시 MCP 도구 사용
3. MCP 도구 없으면 웹 검색
4. 실시간 정보 필요 시 웹 검색 우선

다음 형식으로 응답하세요:
```json
{{
  "selected_tool": "llm|mcp|web_search|none",
  "tool_name": "구체적인 도구 이름 (MCP인 경우)",
  "reasoning": "이 도구를 선택한 이유",
  "params": {{
    "필요한": "파라미터"
  }}
}}
```
"""

# MCP Tool Parameter 생성 프롬프트
MCP_TOOL_PARAM_PROMPT = """MCP 도구 호출을 위한 파라미터를 생성하세요.

도구 이름: {tool_name}
도구 설명: {tool_description}
사용자 요청: {user_request}

파라미터를 JSON 형식으로 생성하세요:
```json
{{
  "param1": "value1",
  "param2": "value2"
}}
```
"""

# Web Search Query 생성 프롬프트
WEB_SEARCH_QUERY_PROMPT = """웹 검색을 위한 최적의 검색어를 생성하세요.

현재 날짜: {current_date}
사용자 요청: {user_input}

## 중요사항
1. "내일", "오늘", "어제" 같은 상대적 날짜는 절대 날짜로 변환하세요
2. 날씨 검색 시 구체적인 날짜를 포함하세요
3. 검색어는 간결하고 핵심적이어야 합니다
4. 최신 정보가 필요한 경우 이를 명시하세요

다음 형식으로 응답하세요:
```json
{{
  "query": "검색어",
  "filters": {{
    "language": "ko",
    "time_range": "recent"
  }}
}}
```
"""

# Result Synthesis 프롬프트
RESULT_SYNTHESIS_PROMPT = """여러 단계의 결과를 통합하여 최종 응답을 생성하세요.

사용자 요청: {user_input}
실행 단계들:
{execution_steps}

## 응답 작성 가이드
1. 사용자 질문에 직접적으로 답변
2. 사용한 도구와 출처 명시
3. 간결하고 명확하게 작성
4. 불확실한 부분은 명시

최종 응답을 작성하세요:
"""

# Memory Save 판단 프롬프트
MEMORY_SAVE_PROMPT = """사용자가 정보를 기억해달라고 요청했는지 판단하세요.

사용자 요청: {user_input}

"기억해", "저장해", "메모해" 등의 명시적 요청이 있는지 확인하세요.

다음 형식으로 응답하세요:
```json
{{
  "should_save": true/false,
  "memory_key": "저장할 키",
  "memory_value": "저장할 값",
  "reasoning": "판단 이유"
}}
```
"""

# Error Handling 프롬프트
ERROR_HANDLING_PROMPT = """오류가 발생했습니다. 대안을 제시하세요.

원래 작업: {original_task}
실패한 도구: {failed_tool}
오류 메시지: {error_message}

## 대안 전략
1. 다른 도구 시도
2. 작업 단순화
3. 사용자에게 추가 정보 요청
4. 부분적 결과 제공

다음 형식으로 응답하세요:
```json
{{
  "alternative_approach": "대안 방법",
  "fallback_tool": "사용할 대체 도구",
  "user_message": "사용자에게 전달할 메시지"
}}
}}
```
"""

# Task Decomposition 프롬프트 (복잡한 작업 분해)
TASK_DECOMPOSITION_PROMPT = """복잡한 작업을 여러 단계로 분해하세요.

사용자 요청: {user_input}

## 분해 기준
1. 각 단계는 독립적으로 실행 가능해야 함
2. 이전 단계의 결과가 다음 단계의 입력이 될 수 있음
3. 실시간 정보가 필요한 단계는 웹 검색 사용
4. 분석/추론이 필요한 단계는 LLM 사용
5. 외부 서비스 호출이 필요한 단계는 MCP 도구 사용

다음 형식으로 응답하세요:
```json
{{
  "steps": [
    {{
      "step_number": 1,
      "action": "작업 설명",
      "tool": "web_search|llm|mcp|memory",
      "description": "이 단계에서 수행할 작업",
      "reasoning": "이 도구를 선택한 이유"
    }}
  ],
  "total_steps": 단계 수
}}
```
"""


def format_prompt(template: str, **kwargs) -> str:
    """
    프롬프트 템플릿 포맷팅
    
    Args:
        template: 프롬프트 템플릿
        **kwargs: 템플릿 변수
    
    Returns:
        포맷팅된 프롬프트
    """
    return template.format(**kwargs)


def get_intent_prompt(user_input: str) -> str:
    """Intent classification 프롬프트 생성"""
    return format_prompt(INTENT_CLASSIFICATION_PROMPT, user_input=user_input)


def get_task_type_prompt(user_input: str) -> str:
    """Task type 분류 프롬프트 생성"""
    return format_prompt(TASK_TYPE_CLASSIFICATION_PROMPT, user_input=user_input)


def get_tool_selection_prompt(task_description: str, available_mcp_tools: list) -> str:
    """Tool selection 프롬프트 생성"""
    tools_str = ", ".join(available_mcp_tools) if available_mcp_tools else "없음"
    return format_prompt(
        TOOL_SELECTION_PROMPT,
        task_description=task_description,
        available_mcp_tools=tools_str
    )


def get_result_synthesis_prompt(user_input: str, execution_steps: list) -> str:
    """Result synthesis 프롬프트 생성"""
    steps_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(execution_steps)])
    return format_prompt(
        RESULT_SYNTHESIS_PROMPT,
        user_input=user_input,
        execution_steps=steps_str
    )


def get_memory_save_prompt(user_input: str) -> str:
    """Memory save 판단 프롬프트 생성"""
    return format_prompt(MEMORY_SAVE_PROMPT, user_input=user_input)


def get_task_decomposition_prompt(user_input: str) -> str:
    """Task decomposition 프롬프트 생성"""
    return format_prompt(TASK_DECOMPOSITION_PROMPT, user_input=user_input)
