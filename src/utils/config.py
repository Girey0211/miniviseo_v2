"""
Configuration Utility

환경변수를 로드하고 설정을 관리합니다.
"""

import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()


class Config:
    """설정 관리 클래스"""
    
    def __init__(self):
        """초기화"""
        self._load_config()
    
    def _load_config(self):
        """환경변수에서 설정 로드"""
        # OpenAI 설정
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # MCP 서버 설정
        self.mcp_servers = self._parse_mcp_servers()
        
        # 로깅 설정
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # 메모리 설정
        self.memory_file = os.getenv("MEMORY_FILE", "data/memory.json")
    
    def _parse_mcp_servers(self) -> Dict[str, Dict[str, str]]:
        """
        MCP 서버 설정 파싱
        
        우선순위:
        1. mcp_servers.json 파일
        2. MCP_SERVERS 환경변수
        
        Returns:
            MCP 서버 딕셔너리
            {
                "server_name": {
                    "url": "server_url",
                    "description": "server_description"
                }
            }
        """
        # 1. JSON 파일에서 로드 시도
        json_file = "mcp_servers.json"
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    servers = json.load(f)
                    return self._validate_mcp_servers(servers, source="mcp_servers.json")
            except json.JSONDecodeError as e:
                print(f"⚠️  경고: {json_file} 파싱 오류: {e}")
            except Exception as e:
                print(f"⚠️  경고: {json_file} 읽기 오류: {e}")
        
        # 2. 환경변수에서 로드 시도 (Fallback)
        mcp_servers_str = os.getenv("MCP_SERVERS", "")
        if mcp_servers_str:
            try:
                servers = json.loads(mcp_servers_str)
                return self._validate_mcp_servers(servers, source="환경변수")
            except json.JSONDecodeError as e:
                print(f"⚠️  경고: MCP_SERVERS 환경변수 파싱 오류: {e}")
        
        # 설정 없음
        return {}
    
    def _validate_mcp_servers(self, servers: Any, source: str) -> Dict[str, Dict[str, str]]:
        """
        MCP 서버 설정 유효성 검증
        
        Args:
            servers: 서버 설정
            source: 설정 출처 (로깅용)
        
        Returns:
            검증된 서버 딕셔너리
        """
        if not isinstance(servers, dict):
            print(f"⚠️  경고: {source}의 MCP 서버 설정이 올바른 딕셔너리 형식이 아닙니다.")
            return {}
        
        # 각 서버 설정 검증
        validated_servers = {}
        for name, config in servers.items():
            if not isinstance(config, dict):
                print(f"⚠️  경고: MCP 서버 '{name}'의 설정이 올바르지 않습니다.")
                continue
            
            if "url" not in config:
                print(f"⚠️  경고: MCP 서버 '{name}'에 url이 없습니다.")
                continue
            
            validated_servers[name] = {
                "url": config["url"],
                "description": config.get("description", "")
            }
        
        if validated_servers:
            print(f"✓ MCP 서버 설정 로드 완료 ({source}): {list(validated_servers.keys())}")
        
        return validated_servers
    
    def get_mcp_server(self, name: str) -> Optional[Dict[str, str]]:
        """
        특정 MCP 서버 설정 가져오기
        
        Args:
            name: 서버 이름
        
        Returns:
            서버 설정 딕셔너리 또는 None
        """
        return self.mcp_servers.get(name)
    
    def has_mcp_servers(self) -> bool:
        """MCP 서버가 설정되어 있는지 확인"""
        return len(self.mcp_servers) > 0
    
    def validate(self) -> bool:
        """
        필수 설정 검증
        
        Returns:
            모든 필수 설정이 유효하면 True
        """
        is_valid = True
        
        if not self.openai_api_key or self.openai_api_key == "your_openai_api_key_here":
            print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
            is_valid = False
        
        if not self.openai_model:
            print("❌ OPENAI_MODEL이 설정되지 않았습니다.")
            is_valid = False
        
        return is_valid
    
    def __repr__(self) -> str:
        """설정 정보 문자열 표현"""
        return (
            f"Config(\n"
            f"  openai_model={self.openai_model},\n"
            f"  mcp_servers={list(self.mcp_servers.keys())},\n"
            f"  log_level={self.log_level},\n"
            f"  memory_file={self.memory_file}\n"
            f")"
        )


# 전역 설정 인스턴스
config = Config()
