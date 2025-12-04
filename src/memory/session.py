"""
Session Memory

단기 세션 메모리를 관리합니다.
"""

from typing import Dict, Any, List, Optional
from src.memory.storage import MemoryStorage
from src.utils.logger import setup_logger

logger = setup_logger("session_memory")


class SessionMemory:
    """세션 메모리 관리 클래스"""
    
    def __init__(self, max_history: int = 10):
        """
        초기화
        
        Args:
            max_history: 유지할 최대 대화 수
        """
        self.storage = MemoryStorage()
        self.max_history = max_history
        logger.info(f"Session Memory 초기화 (Max History: {max_history})")
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """
        메시지 추가
        
        Args:
            role: 역할 (user/assistant/system)
            content: 내용
            metadata: 추가 메타데이터
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": None,  # TODO: 타임스탬프 추가
            "metadata": metadata or {}
        }
        
        self.storage.add_session_memory(message)
        self._prune_history()
        
        logger.debug(f"세션 메시지 추가: {role}")
    
    def get_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        대화 기록 가져오기
        
        Args:
            limit: 가져올 개수 제한
        
        Returns:
            메시지 리스트
        """
        history = self.storage.get_session_memory()
        
        if limit:
            return history[-limit:]
        return history
    
    def get_context_string(self, limit: int = 5) -> str:
        """
        컨텍스트 문자열 생성 (프롬프트용)
        
        Args:
            limit: 포함할 최근 메시지 수
        
        Returns:
            포맷팅된 대화 기록
        """
        history = self.get_history(limit)
        context = []
        
        for msg in history:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                context.append(f"User: {content}")
            elif role == "assistant":
                context.append(f"Assistant: {content}")
            elif role == "system":
                context.append(f"System: {content}")
        
        return "\n".join(context)
    
    def clear(self):
        """세션 초기화"""
        self.storage.clear_session_memory()
        logger.info("세션 메모리 초기화됨")
    
    def _prune_history(self):
        """오래된 기록 정리"""
        history = self.storage.get_session_memory()
        if len(history) > self.max_history:
            # 저장소 구현에 따라 효율적인 방법으로 변경 필요
            # 현재는 전체 로드 후 슬라이싱하여 재저장하는 방식이라 비효율적일 수 있음
            # MemoryStorage에 prune 메서드를 추가하는 것이 좋음
            pass
