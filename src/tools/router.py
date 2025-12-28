"""
Tool Router

적절한 도구를 선택하고 호출을 라우팅합니다.
"""

from typing import Dict, Any, Optional, List
from src.utils.logger import setup_logger
from src.tools.mcp_client import MCPClient
from src.tools.web_search import WebSearch

logger = setup_logger("tool_router")


class ToolRouter:
    """도구 라우터 클래스"""
    
    def __init__(self):
        """초기화"""
        self.mcp_client = MCPClient()
        self.web_search = WebSearch()
        logger.info("Tool Router 초기화 완료")
    
    def route_tool_call(
        self,
        tool_type: str,
        tool_name: str,
        params: Dict[str, Any],
        user_input: str
    ) -> Any:
        """
        도구 호출 라우팅
        
        Args:
            tool_type: 도구 타입 (mcp, web_search 등)
            tool_name: 도구 이름
            params: 파라미터
            user_input: 사용자 입력 (필요시 사용)
        
        Returns:
            도구 실행 결과
        """
        logger.info(f"도구 라우팅: {tool_type} - {tool_name}")
        
        if tool_type == "mcp":
            return self._handle_mcp_call(tool_name, params)
        
        elif tool_type == "web_search":
            return self._handle_web_search(user_input, params)
        
        else:
            logger.warning(f"알 수 없는 도구 타입: {tool_type}")
            return None
    
    def _handle_mcp_call(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """MCP 도구 호출 처리"""
        # 서버 이름과 도구 이름 분리 (예: notion.create_page)
        if "." in tool_name:
            server_name, actual_tool_name = tool_name.split(".", 1)
        else:
            # 기본 서버 가정 또는 검색
            # 여기서는 간단히 첫 번째 서버 사용 또는 에러
            servers = self.mcp_client.list_servers()
            if servers:
                server_name = servers[0]
                actual_tool_name = tool_name
            else:
                logger.error("사용 가능한 MCP 서버가 없습니다.")
                return None
        
        # 서버 연결 확인 및 연결
        if server_name not in self.mcp_client.sessions:
            logger.warning(f"MCP 서버 {server_name}에 연결되어 있지 않습니다.")
            return None
        
        # 도구 호출
        result = self.mcp_client.call_tool(server_name, actual_tool_name, params)
        
        if result is None:
            # 실패 시 fallback 로직은 Executor에서 처리하지만,
            # 여기서는 기본적인 에러 메시지 반환 가능
            return f"MCP 도구 호출 실패: {tool_name}"
            
        return result
    
    def _handle_web_search(self, user_input: str, params: Dict[str, Any]) -> str:
        """웹 검색 처리"""
        # 1. 검색어 생성 (파라미터에 query가 없으면 자동 생성)
        query = params.get("query")
        if not query:
            query_info = self.web_search.generate_query(user_input)
            query = query_info.get("query", user_input)
        
        # 2. 검색 실행
        results = self.web_search.search(query)
        
        # 3. 결과 요약
        summary = self.web_search.summarize_results(results, query)
        
        return summary
    
    def get_available_tools(self) -> List[str]:
        """사용 가능한 모든 도구 목록 반환"""
        tools = []
        
        # MCP 도구
        for server in self.mcp_client.list_servers():
            server_tools = self.mcp_client.get_available_tools(server)
            tools.extend([f"{server}.{tool}" for tool in server_tools])
        
        # 웹 검색은 항상 가능
        tools.append("web_search")
        
        return tools
