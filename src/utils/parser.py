"""
Input Parser

사용자 입력을 분석하고 의도를 파악합니다.
"""

from typing import Dict, Any, Optional
from enum import Enum


class TaskType(Enum):
    """작업 타입 열거형"""
    SIMPLE_QUERY = "simple_query"  # 단순 질문
    TOOL_REQUIRED = "tool_required"  # 툴 사용 필요
    WEB_SEARCH = "web_search"  # 웹 검색 필요
    MEMORY_QUERY = "memory_query"  # 메모리 조회
    COMPLEX_CHAIN = "complex_chain"  # 복합 체이닝


class InputParser:
    """사용자 입력 파싱 클래스"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def parse(self, user_input: str) -> Dict[str, Any]:
        """
        사용자 입력 파싱
        
        Args:
            user_input: 사용자 입력 문자열
        
        Returns:
            파싱 결과 딕셔너리
            {
                "original_input": str,
                "task_type": TaskType,
                "intent": str,
                "entities": dict
            }
        """
        # TODO: LLM 기반 의도 분류 구현
        # 현재는 기본 구조만 반환
        
        return {
            "original_input": user_input,
            "task_type": TaskType.SIMPLE_QUERY,
            "intent": "unknown",
            "entities": {}
        }
    
    def extract_entities(self, user_input: str) -> Dict[str, Any]:
        """
        입력에서 엔티티 추출
        
        Args:
            user_input: 사용자 입력
        
        Returns:
            추출된 엔티티 딕셔너리
        """
        # TODO: 날짜, 파일명, URL 등 엔티티 추출 로직 구현
        return {}
    
    def classify_task_type(self, user_input: str) -> TaskType:
        """
        작업 타입 분류
        
        Args:
            user_input: 사용자 입력
        
        Returns:
            TaskType
        """
        # TODO: LLM 기반 작업 타입 분류 구현
        return TaskType.SIMPLE_QUERY
