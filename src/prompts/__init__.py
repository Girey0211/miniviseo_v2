"""Prompts 패키지 - 프롬프트 템플릿 관리"""

from .system import (
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_WITH_MEMORY,
    CHAINING_SYSTEM_PROMPT,
    get_system_prompt,
    get_chaining_prompt
)

from .templates import (
    get_intent_prompt,
    get_task_type_prompt,
    get_tool_selection_prompt,
    get_result_synthesis_prompt,
    get_memory_save_prompt,
    get_task_decomposition_prompt,
    get_mcp_tool_param_prompt,
    format_prompt
)

__all__ = [
    # System prompts
    'get_system_prompt',
    'get_system_prompt_with_memory',
    'get_chaining_prompt', # Renamed from get_chaining_system_prompt in the instruction, keeping original name
    
    # Template prompts
    'get_intent_prompt',
    'get_task_type_prompt',
    'get_tool_selection_prompt',
    'get_result_synthesis_prompt',
    'get_memory_save_prompt',
    'get_task_decomposition_prompt',
    'get_mcp_tool_param_prompt',
    'format_prompt'
]
