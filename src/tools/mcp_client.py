"""
MCP Client

MCP 서버와 통신하는 클라이언트입니다.
mcp 라이브러리를 사용하여 구현되었습니다.
"""

import asyncio
from typing import Dict, Any, Optional, List
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.utils.config import config
from src.utils.logger import setup_logger

logger = setup_logger("mcp_client")


class MCPClient:
    """MCP 클라이언트 클래스"""
    
    def __init__(self):
        """초기화"""
        self.servers_config = config.mcp_servers
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        
        if config.has_mcp_servers():
            logger.info(f"MCP 서버 설정 로드: {list(self.servers_config.keys())}")
        else:
            logger.info("설정된 MCP 서버가 없습니다.")
    
    async def connect_server(self, server_name: str) -> bool:
        """
        MCP 서버에 연결 (비동기)
        
        Args:
            server_name: 서버 이름
        
        Returns:
            연결 성공 여부
        """
        if server_name not in self.servers_config:
            logger.error(f"MCP 서버 '{server_name}'를 찾을 수 없습니다.")
            return False
        
        if server_name in self.sessions:
            return True
            
        server_config = self.servers_config[server_name]
        url = server_config["url"]
        
        logger.info(f"MCP 서버 연결 시도: {server_name} ({url})")
        
        try:
            # TODO: URL 스키마에 따라 SSE 또는 Stdio 연결 분기
            # 현재는 예시로 Stdio 연결 구조만 보여줌 (실제로는 URL 파싱 필요)
            
            # 주의: 실제 구현에서는 URL이 http/https이면 SSE 클라이언트를 사용해야 함
            # 여기서는 mcp 라이브러리의 사용법을 보여주기 위한 구조임
            
            # 예: Stdio 연결 (로컬 실행 파일)
            # server_params = StdioServerParameters(command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", "/Users/mac/Desktop"])
            # stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            # session = await self.exit_stack.enter_async_context(ClientSession(stdio_transport[0], stdio_transport[1]))
            # await session.initialize()
            
            # 현재는 실제 연결 없이 성공으로 처리 (시뮬레이션)
            self.sessions[server_name] = "mock_session"
            logger.info(f"MCP 서버 연결 성공: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"MCP 서버 연결 실패: {e}")
            return False
    
    async def disconnect_server(self, server_name: str):
        """
        MCP 서버 연결 해제
        
        Args:
            server_name: 서버 이름
        """
        if server_name in self.sessions:
            del self.sessions[server_name]
            logger.info(f"MCP 서버 연결 해제: {server_name}")
            
    async def cleanup(self):
        """리소스 정리"""
        await self.exit_stack.aclose()
    
    def get_available_tools(self, server_name: str = None) -> List[str]:
        """
        사용 가능한 툴 목록 가져오기
        
        Args:
            server_name: 특정 서버 이름 (None이면 모든 서버)
        
        Returns:
            툴 이름 리스트
        """
        # TODO: 실제 세션에서 툴 목록 조회
        # tools = await session.list_tools()
        
        # 모의 데이터 반환
        if server_name == "notion":
            return ["create_page", "search_page", "update_page"]
        return []
    
    def call_tool(
        self,
        server_name: str,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        MCP 툴 호출 (동기 래퍼)
        
        Args:
            server_name: 서버 이름
            tool_name: 툴 이름
            params: 파라미터
        
        Returns:
            툴 실행 결과
        """
        # 비동기 호출을 동기로 처리하기 위한 래퍼
        # 실제 앱에서는 전체가 비동기여야 함
        try:
            # loop = asyncio.get_event_loop()
            # return loop.run_until_complete(self._call_tool_async(server_name, tool_name, params))
            
            # 시뮬레이션 결과 반환
            if server_name not in self.sessions:
                # 자동 연결 시도 (동기 환경에서는 제한적)
                logger.warning(f"서버 {server_name}에 연결되어 있지 않습니다.")
                return None
                
            logger.info(f"MCP 툴 호출 실행: {server_name}.{tool_name}")
            return {
                "status": "success",
                "message": f"{tool_name} executed successfully with params {params}",
                "data": {"id": "12345", "type": "page"}
            }
            
        except Exception as e:
            logger.error(f"툴 호출 오류: {e}")
            return None

    async def _call_tool_async(
        self,
        server_name: str,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        MCP 툴 호출 (비동기)
        """
        if server_name not in self.sessions:
            connected = await self.connect_server(server_name)
            if not connected:
                return None
        
        # session = self.sessions[server_name]
        # result = await session.call_tool(tool_name, arguments=params)
        # return result
        return None
    
    def list_servers(self) -> List[str]:
        """서버 목록 반환"""
        return list(self.servers_config.keys())
    
    def get_server_info(self, server_name: str) -> Optional[Dict[str, str]]:
        """서버 정보 반환"""
        return self.servers_config.get(server_name)
