"""
Persistent Memory

장기 메모리를 관리합니다.
"""

from typing import Dict, Any, List, Optional
from src.memory.storage import MemoryStorage
from src.utils.logger import setup_logger
from src.utils.openai_client import get_openai_client
from src.prompts.templates import get_memory_save_prompt

logger = setup_logger("persistent_memory")


class PersistentMemory:
    """장기 메모리 관리 클래스"""
    
    def __init__(self):
        """초기화"""
        self.storage = MemoryStorage()
        self.openai_client = get_openai_client()
        logger.info("Persistent Memory 초기화 완료")
    
    def remember(self, key: str, value: Any):
        """
        정보 기억하기
        
        Args:
            key: 키
            value: 값
        """
        self.storage.set_long_term_memory(key, value)
        logger.info(f"장기 메모리 저장: {key}")
    
    def recall(self, key: str = None) -> Any:
        """
        정보 불러오기
        
        Args:
            key: 키 (None이면 전체)
        
        Returns:
            저장된 값
        """
        return self.storage.get_long_term_memory(key)
    
    def forget(self, key: str):
        """
        정보 잊기
        
        Args:
            key: 키
        """
        self.storage.remove_long_term_memory(key)
        logger.info(f"장기 메모리 삭제: {key}")
    
    def analyze_and_remember(self, user_input: str, context: str = "") -> Optional[Dict[str, Any]]:
        """
        사용자 입력을 분석하여 필요한 경우 기억하기
        
        Args:
            user_input: 사용자 입력
            context: 대화 맥락
        
        Returns:
            저장된 정보 또는 None
        """
        try:
            prompt = get_memory_save_prompt(user_input, context)
            result = self.openai_client.query_with_json(
                system_prompt="당신은 사용자의 중요한 정보를 기억하는 메모리 관리자입니다.",
                user_message=prompt
            )
            
            if result and result.get("should_save"):
                key = result.get("memory_key")
                value = result.get("memory_value")
                
                if key and value:
                    self.remember(key, value)
                    return {"key": key, "value": value}
            
            return None
            
        except Exception as e:
            logger.error(f"메모리 분석 오류: {e}")
            return None
    
    def get_memory_string(self) -> str:
        """
        메모리 문자열 생성 (프롬프트용)
        
        Returns:
            포맷팅된 메모리 내용
        """
        memories = self.recall()
        if not memories:
            return "저장된 메모리가 없습니다."
        
        memory_list = []
        for k, v in memories.items():
            memory_list.append(f"- {k}: {v}")
        
        return "\n".join(memory_list)
