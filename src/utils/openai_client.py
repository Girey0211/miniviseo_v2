"""
OpenAI Client

OpenAI API와 통신하는 클라이언트입니다.
"""

import json
from typing import Dict, Any, Optional, List
from openai import OpenAI
from src.utils.config import config
from src.utils.logger import setup_logger

logger = setup_logger("openai_client")


class OpenAIClient:
    """OpenAI API 클라이언트"""
    
    def __init__(self):
        """초기화"""
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = config.openai_model
        logger.info(f"OpenAI Client 초기화 완료 (모델: {self.model})")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False
    ) -> str:
        """
        Chat completion 요청
        
        Args:
            messages: 메시지 리스트 [{"role": "user", "content": "..."}]
            temperature: 온도 (0.0-2.0)
            max_tokens: 최대 토큰 수
            json_mode: JSON 모드 활성화
        
        Returns:
            응답 텍스트
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            logger.debug(f"OpenAI API 호출: {len(messages)} 메시지")
            
            response = self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            logger.debug(f"OpenAI API 응답: {len(content)} 문자")
            
            return content
            
        except Exception as e:
            logger.error(f"OpenAI API 오류: {e}")
            raise
    
    def parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        JSON 응답 파싱
        
        Args:
            response: 응답 텍스트
        
        Returns:
            파싱된 JSON 딕셔너리 또는 None
        """
        try:
            # 코드 블록 제거
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            logger.debug(f"원본 응답: {response}")
            return None
    
    def simple_query(self, system_prompt: str, user_message: str) -> str:
        """
        간단한 질의응답
        
        Args:
            system_prompt: 시스템 프롬프트
            user_message: 사용자 메시지
        
        Returns:
            응답 텍스트
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return self.chat_completion(messages)
    
    def query_with_json(
        self,
        system_prompt: str,
        user_message: str
    ) -> Optional[Dict[str, Any]]:
        """
        JSON 응답을 요청하는 질의
        
        Args:
            system_prompt: 시스템 프롬프트
            user_message: 사용자 메시지
        
        Returns:
            파싱된 JSON 딕셔너리
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        response = self.chat_completion(messages, json_mode=True)
        return self.parse_json_response(response)


# 전역 클라이언트 인스턴스
_client_instance = None


def get_openai_client() -> OpenAIClient:
    """
    OpenAI 클라이언트 싱글톤 인스턴스 가져오기
    
    Returns:
        OpenAIClient 인스턴스
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = OpenAIClient()
    return _client_instance
