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
from mcp.client.sse import sse_client

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
        
        # 백그라운드 스레드와 이벤트 루프 생성
        self._loop = None
        self._thread = None
        self._setup_background_loop()
        
        if config.has_mcp_servers():
            logger.info(f"MCP 서버 {len(self.servers_config)}개 발견:")
            for name, server_config in self.servers_config.items():
                cmd = server_config.get('command', 'unknown')
                args = ' '.join(server_config.get('args', []))
                cmd_str = f"{cmd} {args}".strip()
                desc = server_config.get('description', 'No description')
                logger.info(f"  - {name}: {cmd_str} ({desc})")
            
            # 모든 서버에 비동기 연결 및 도구 목록 조회 시작
            logger.info("모든 승인된 MCP 서버에 연결을 시도하고 도구 목록을 조회합니다...")
            asyncio.run_coroutine_threadsafe(self._connect_all_servers(), self._loop)
        else:
            logger.info("설정된 MCP 서버가 없습니다.")
    
    def _setup_background_loop(self):
        """백그라운드 이벤트 루프 설정"""
        import threading
        
        def run_loop(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()
        
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=run_loop, args=(self._loop,), daemon=True)
        self._thread.start()
        logger.debug("백그라운드 이벤트 루프 시작됨")
    
    def _run_in_loop(self, coro):
        """백그라운드 루프에서 코루틴 실행"""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=30)
    
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
            logger.debug(f"서버 {server_name}는 이미 연결되어 있습니다.")
            return True
            
        server_config = self.servers_config[server_name]
        
        logger.info(f"MCP 서버 연결 시도: {server_name}")
        
        try:
            # 서버 타입 감지 (url이 있으면 HTTP, command가 있으면 stdio)
            server_type = server_config.get("type")
            if not server_type:
                # type이 명시되지 않은 경우 자동 감지
                if "url" in server_config:
                    server_type = "http"
                elif "command" in server_config:
                    server_type = "stdio"
                else:
                    logger.error(f"서버 {server_name}에 'url' 또는 'command'가 설정되지 않았습니다.")
                    return False
            
            logger.info(f"서버 타입: {server_type}")
            
            # 서버 타입에 따라 다른 연결 방식 사용
            if server_type == "http":
                # HTTP/SSE 연결
                url = server_config.get("url")
                if not url:
                    logger.error(f"서버 {server_name}에 url이 설정되지 않았습니다.")
                    return False
                
                logger.info(f"HTTP 연결 시도: {url}")
                
                # SSE 클라이언트로 HTTP 연결
                sse_transport = await self.exit_stack.enter_async_context(
                    sse_client(url)
                )
                read, write = sse_transport
                
                # 클라이언트 세션 생성 및 초기화
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
                await session.initialize()
                
            elif server_type == "stdio":
                # Stdio 연결
                command = server_config.get("command")
                args = server_config.get("args", [])
                
                if not command:
                    logger.error(f"서버 {server_name}에 command가 설정되지 않았습니다.")
                    return False
                
                # Stdio 서버 파라미터 설정
                server_params = StdioServerParameters(
                    command=command,
                    args=args,
                    env=None
                )
                
                # Stdio 클라이언트로 전송 채널 생성
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                stdio, write = stdio_transport
                
                # 클라이언트 세션 생성 및 초기화
                session = await self.exit_stack.enter_async_context(
                    ClientSession(stdio, write)
                )
                await session.initialize()
                
            else:
                logger.error(f"지원하지 않는 서버 타입: {server_type}")
                return False
            
            # 세션 저장
            self.sessions[server_name] = session
            
            # 도구 목록 가져오기
            response = await session.list_tools()
            tools = [tool.name for tool in response.tools]
            
            logger.info(f"MCP 서버 연결 성공: {server_name}, 도구: {tools}")
            
            # 각 도구의 스키마를 상세하게 로그하지 않고, 위에서 이미 리스트로 로깅함
            # logger.info(f"MCP 서버 연결 성공: {server_name}, 도구: {tools}")
            
            return True
            
        except Exception as e:
            logger.error(f"MCP 서버 연결 실패 ({server_name}): {e}")
            import traceback
            traceback.print_exc()
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
    
    async def _connect_all_servers(self):
        """모든 설정된 서버에 연결하고 도구 목록을 로깅"""
        for name in self.servers_config:
            try:
                # 연결 및 도구 목록 가져오기 (이미 get_available_tools 내부에서 로깅함)
                # _get_available_tools_async는 연결도 수행함
                await self._get_available_tools_async(name)
            except Exception as e:
                logger.error(f"서버 {name} 초기화 중 오류: {e}")
    
    def get_available_tools(self, server_name: str = None) -> List[str]:
        """
        사용 가능한 툴 목록 가져오기 (동기 래퍼)
        
        Args:
            server_name: 서버 이름
        
        Returns:
            툴 이름 리스트
        """
        if server_name not in self.servers_config:
            logger.warning(f"서버 '{server_name}'를 찾을 수 없습니다.")
            return []
        
        try:
            return self._run_in_loop(self._get_available_tools_async(server_name))
        except Exception as e:
            logger.error(f"도구 목록 조회 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _get_available_tools_async(self, server_name: str) -> List[str]:
        """
        사용 가능한 툴 목록 가져오기 (비동기)
        
        Args:
            server_name: 서버 이름
        
        Returns:
            툴 이름 리스트
        """
        # 서버에 연결되어 있지 않으면 연결 시도
        if server_name not in self.sessions:
            logger.info(f"MCP 서버 '{server_name}' 연결 시도 중...")
            connected = await self.connect_server(server_name)
            if connected:
                logger.info(f"✓ MCP 서버 '{server_name}' 연결 성공")
            else:
                logger.warning(f"✗ MCP 서버 '{server_name}' 연결 실패")
                return []
        
        session = self.sessions[server_name]
        
        try:
            # 세션에서 도구 목록 가져오기
            response = await session.list_tools()
            tools = [tool.name for tool in response.tools]
            
            # 도구 스키마 정보도 저장 (캐싱)
            if not hasattr(self, '_tools_schema'):
                self._tools_schema = {}
            
            for tool in response.tools:
                tool_key = f"{server_name}.{tool.name}"
                self._tools_schema[tool_key] = {
                    "name": tool.name,
                    "description": tool.description if hasattr(tool, 'description') else "",
                    "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                }
                # 상세 스키마 로깅 제거
            
            logger.info(f"서버 {server_name}에서 {len(tools)}개 도구 발견: {tools}")
            return tools
        except Exception as e:
            logger.error(f"도구 목록 조회 실패: {e}")
            return []
    
    def get_tool_schema(self, tool_key: str) -> Dict[str, Any]:
        """
        도구 스키마 정보 반환
        
        Args:
            tool_key: "서버명.도구명" 형식
        
        Returns:
            도구 스키마
        """
        if not hasattr(self, '_tools_schema'):
            return {}
        return self._tools_schema.get(tool_key, {})
    
    def get_all_tools_schema(self) -> Dict[str, Dict[str, Any]]:
        """모든 도구의 스키마 정보 반환"""
        if not hasattr(self, '_tools_schema'):
            return {}
        return self._tools_schema
    
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
        logger.info(f"MCP 도구 호출 시작: {server_name}.{tool_name}")
        logger.info(f"파라미터: {params}")
        
        try:
            return self._run_in_loop(self._call_tool_async(server_name, tool_name, params))
        except Exception as e:
            logger.error(f"MCP 도구 호출 오류: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _call_tool_async(
        self,
        server_name: str,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        MCP 툴 호출 (비동기)
        
        Args:
            server_name: 서버 이름
            tool_name: 툴 이름
            params: 파라미터
        
        Returns:
            툴 실행 결과
        """
        # 서버에 연결되어 있지 않으면 연결 시도
        if server_name not in self.sessions:
            logger.warning(f"서버 {server_name}에 연결되어 있지 않습니다. 연결 시도 중...")
            connected = await self.connect_server(server_name)
            if not connected:
                logger.error(f"서버 {server_name} 연결 실패")
                return None
        
        session = self.sessions[server_name]
        
        try:
            logger.info(f"MCP 세션을 통해 도구 호출: {tool_name}, 파라미터: {params}")
            
            # 실제 MCP 서버 도구 호출
            result = await session.call_tool(tool_name, arguments=params)
            
            logger.info(f"MCP 도구 호출 성공: {tool_name}")
            logger.info(f"반환값 타입: {type(result)}")
            logger.info(f"반환값 내용: {result}")
            
            # result 객체 파싱
            if hasattr(result, 'content'):
                content = result.content
                logger.info(f"반환 content: {content}")
                
                # content가 리스트인 경우
                if isinstance(content, list) and len(content) > 0:
                    first_item = content[0]
                    logger.info(f"첫 번째 아이템 타입: {type(first_item)}")
                    
                    # TextContent 객체인 경우
                    if hasattr(first_item, 'text'):
                        logger.info(f"텍스트 내용: {first_item.text}")
                        return {"success": True, "result": first_item.text}
                    else:
                        logger.info(f"첫 번째 아이템: {first_item}")
                        return {"success": True, "result": str(first_item)}
                else:
                    return {"success": True, "result": str(content)}
            else:
                logger.info(f"result 객체 전체: {result}")
                return {"success": True, "result": str(result)}
            
        except Exception as e:
            logger.error(f"MCP 도구 호출 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def list_servers(self) -> List[str]:
        """서버 목록 반환"""
        return list(self.servers_config.keys())
    
    def get_server_info(self, server_name: str) -> Optional[Dict[str, str]]:
        """서버 정보 반환"""
        return self.servers_config.get(server_name)
