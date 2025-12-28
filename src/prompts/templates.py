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

# Tool Selection# 도구 선택 프롬프트
TOOL_SELECTION_PROMPT = """작업을 수행하기 위한 최적의 도구를 선택하고 파라미터를 생성하세요.

{current_date_info}

[이전 대화 맥락]:
{context}

작업: {task_description}
사용 가능한 MCP 도구: {available_mcp_tools}
{schema_details}

**중요 규칙:**
1. 작업에 가장 적합한 도구 선택
2. 외부 데이터/서비스 필요 시 MCP 도구 사용
3. MCP 도구 없으면 웹 검색
4. 실시간 정보 필요 시 웹 검색 우선

**파라미터 생성 규칙 (매우 중요!):**
1. **반드시 위의 "사용 가능한 도구 상세 정보"에 명시된 정확한 파라미터 이름을 사용하세요**
2. **[필수] 표시된 파라미터는 반드시 모두 포함해야 합니다**
3. **파라미터 이름을 임의로 변경하거나 추측하지 마세요**
4. **스키마에 명시된 타입(string, number 등)을 준수하세요**
5. **날짜는 YYYY-MM-DD 형식, 날짜+시간은 YYYY-MM-DDTHH:MM:SS 형식을 사용하세요**
6. **"내일", "다음주" 등 상대적 날짜는 위의 현재 날짜 정보를 기준으로 계산하세요**
7. **날짜/시간은 반드시 한국 시간대(KST, +09:00)를 포함해야 합니다.**
7. **날짜/시간은 반드시 한국 시간대(KST, +09:00)를 포함해야 합니다.**
8. **사용자 요청의 세부 정보를 반영하여 의미 있는 값을 생성하세요**
9. **[중요] 사용자가 "그거", "이전 내용", "검색 결과" 등 문맥을 참조하는 경우, 반드시 [이전 대화 맥락]에서 구체적인 내용을 추출하여 파라미터에 포함하세요. (예: "맛집" -> 실제 찾은 식당 이름들 나열)**

예시:
- 사용자: "내일 오후 3시에 회의" → `{{"title": "회의", "date": "2025-12-09T15:00:00+09:00"}}`
- 사용자: "저녁 약속 일정" → `{{"title": "저녁 약속", "date": "2025-12-08T19:00:00+09:00"}}`
- 스키마에 `event_title`이 있다면 → `{{"event_title": "회의"}}`
- 임의로 파라미터 이름을 바꾸지 마세요!

다음 형식으로 응답하세요:
```json
{{
  "selected_tool": "llm|mcp|web_search|none",
  "tool_name": "구체적인 도구 이름 (예: notion.add_calendar_event)",
  "reasoning": "이 도구를 선택한 이유",
  "params": {{
    "스키마에_명시된_정확한_파라미터_이름": "사용자_요청을_반영한_값"
  }}
}}
```
"""

# MCP Tool Parameter 생성 프롬프트
MCP_TOOL_PARAM_PROMPT = """MCP 도구 호출을 위한 파라미터를 생성하세요.

도구 이름: {tool_name}
도구 설명: {tool_description}

## 파라미터 스키마 (각 파라미터의 설명을 주의 깊게 읽으세요!)
{parameter_schema}

사용자 요청: {user_request}

## 중요 지침
1. **파라미터의 설명(description)을 보고 가장 적절한 필드에 데이터를 넣으세요.**
    - 검색 결과나 요약 내용이 있다면, 이를 담을 수 있는 필드(예: `description`, `body`, `content`, `summary` 등)를 찾아 상세히 기록하세요.
    - 단순히 "검색 결과"라고 쓰지 말고, 실제로 검색된 **모든 중요한 세부 정보**를 포함하세요.
2. 날짜/시간 포맷: **반드시 한국 시간대(KST, +09:00)를 포함하세요.** (예: 2024-01-01T10:00:00+09:00)
3. 누락된 정보가 있다면 사용자 요청 내에서 합리적으로 추론하거나 기본값을 사용하세요.
4. **[중요] "저장해줘", "메모해줘" 등의 요청 시, 사용자가 가리키는 대상(예: 검색된 맛집 목록)을 [이전 단계 실행 결과]나 [이전 대화 맥락]에서 찾아 상세히 기술하세요.**

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
[이전 대화 맥락]:
{context}

"기억해", "저장해", "메모해" 등의 명시적 요청이 있는지 확인하세요.

**중요**: "그거", "방금 검색한 거" 등 대명사를 사용하는 경우, **[이전 대화 맥락]에서 구체적인 내용을 찾아 `memory_value`에 저장하세요.** (예: "방금 찾은 맛집" -> "A식당, B식당, C식당")

다음 형식으로 응답하세요:
```json
{{
  "should_save": true/false,
  "memory_key": "저장할 키",
  "memory_value": "저장할 값 (문맥에서 추출한 구체적 내용)",
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


def get_tool_selection_prompt(task_description: str, available_mcp_tools: list, tools_schema: dict = None, context: str = "") -> str:
    """Tool selection 프롬프트 생성"""
    from datetime import datetime
    
    tools_str = ", ".join(available_mcp_tools) if available_mcp_tools else "없음"
    
    # 현재 날짜 정보
    now = datetime.now()
    current_date_info = f"""
현재 날짜 및 시간 (KST): {now.strftime('%Y-%m-%d %H:%M:%S')}
- 오늘: {now.strftime('%Y-%m-%d')}
- 현재 시각: {now.strftime('%H:%M')}
- 시간대: Asia/Seoul (+09:00)
"""
    
    # 도구 스키마 정보를 상세하게 포맷팅
    schema_details = ""
    if tools_schema:
        schema_details = "\n\n## 사용 가능한 도구 상세 정보:\n"
        for tool_key, schema in tools_schema.items():
            schema_details += f"\n### {tool_key}\n"
            schema_details += f"- 설명: {schema.get('description', '설명 없음')}\n"
            
            input_schema = schema.get('inputSchema', {})
            if input_schema:
                schema_details += f"- 파라미터:\n"
                properties = input_schema.get('properties', {})
                required = input_schema.get('required', [])
                
                for prop_name, prop_info in properties.items():
                    is_required = "**필수**" if prop_name in required else "선택"
                    prop_type = prop_info.get('type', 'any')
                    prop_desc = prop_info.get('description', '')
                    default_val = prop_info.get('default', '')
                    
                    param_line = f"  - `{prop_name}` ({prop_type}) [{is_required}]"
                    if prop_desc:
                        param_line += f": {prop_desc}"
                    if default_val:
                        param_line += f" (기본값: {default_val})"
                    schema_details += param_line + "\n"
            
    return format_prompt(
        TOOL_SELECTION_PROMPT,
        task_description=task_description,
        available_mcp_tools=tools_str,
        current_date_info=current_date_info,
        schema_details=schema_details,
        context=context
    )


def get_result_synthesis_prompt(user_input: str, execution_steps: list) -> str:
    """Result synthesis 프롬프트 생성"""
    steps_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(execution_steps)])
    return format_prompt(
        RESULT_SYNTHESIS_PROMPT,
        user_input=user_input,
        execution_steps=steps_str
    )


def get_memory_save_prompt(user_input: str, context: str = "") -> str:
    """Memory save 판단 프롬프트 생성"""
    return format_prompt(MEMORY_SAVE_PROMPT, user_input=user_input, context=context)


def get_task_decomposition_prompt(user_input: str) -> str:
    """Task decomposition 프롬프트 생성"""
    return format_prompt(TASK_DECOMPOSITION_PROMPT, user_input=user_input)


def get_mcp_tool_param_prompt(tool_name: str, tool_description: str, parameter_schema: str, user_request: str) -> str:
    """MCP tool param generation 프롬프트 생성"""
    return format_prompt(
        MCP_TOOL_PARAM_PROMPT,
        tool_name=tool_name,
        tool_description=tool_description,
        parameter_schema=parameter_schema,
        user_request=user_request
    )
