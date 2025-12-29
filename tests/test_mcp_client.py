
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from src.tools.mcp_client import MCPClient

class TestMCPClient(unittest.TestCase):
    def setUp(self):
        self.client = MCPClient()
        # Disable background loop for testing to control execution
        if self.client._thread:
             # Just let it run, we won't use it directly in these unit tests
             # or we could try to stop it if needed, but for now it's fine.
             pass

    @patch('src.tools.mcp_client.sse_client')
    @patch('src.tools.mcp_client.ClientSession')
    def test_connect_http_server(self, mock_session_cls, mock_sse_client):
        """HTTP 서버 연결 및 타입 감지 테스트"""
        async def run_test():
            # Mock setup
            mock_sse_transport = AsyncMock()
            # __aenter__ returns the transport (read, write)
            mock_sse_transport.__aenter__.return_value = (MagicMock(), MagicMock())
            mock_sse_client.return_value = mock_sse_transport
            
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session_cls.return_value = mock_session
            
            # Setup configuration
            self.client.servers_config = {
                "test_http": {
                    "url": "http://localhost:8000/sse",
                    "description": "Test HTTP Server"
                }
            }
            
            # Execute
            result = await self.client.connect_server("test_http")
            
            # Verify
            self.assertTrue(result)
            mock_sse_client.assert_called_with("http://localhost:8000/sse")
            self.assertIn("test_http", self.client.sessions)
            
        # Run async test
        asyncio.run(run_test())

    @patch('src.tools.mcp_client.stdio_client')
    @patch('src.tools.mcp_client.ClientSession')
    def test_connect_stdio_server(self, mock_session_cls, mock_stdio_client):
        """Stdio 서버 연결 및 타입 감지 테스트"""
        async def run_test():
            # Mock setup
            mock_stdio_transport = AsyncMock()
            mock_stdio_transport.__aenter__.return_value = (MagicMock(), MagicMock())
            mock_stdio_client.return_value = mock_stdio_transport
            
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session_cls.return_value = mock_session
            
            # Setup configuration
            self.client.servers_config = {
                "test_stdio": {
                    "command": "python",
                    "args": ["server.py"],
                    "description": "Test Stdio Server"
                }
            }
            
            # Execute
            result = await self.client.connect_server("test_stdio")
            
            # Verify
            self.assertTrue(result)
            # Check if stdio_client was called (arguments verification omitted for brevity)
            self.assertTrue(mock_stdio_client.called)
            self.assertIn("test_stdio", self.client.sessions)

        # Run async test
        asyncio.run(run_test())

    @patch('src.tools.mcp_client.sse_client')
    @patch('src.tools.mcp_client.ClientSession')
    def test_explicit_type_http(self, mock_session_cls, mock_sse_client):
        """명시적 type='http' 설정 테스트"""
        async def run_test():
            # Mock setup (simplified)
            mock_sse_transport = AsyncMock()
            mock_sse_transport.__aenter__.return_value = (MagicMock(), MagicMock())
            mock_sse_client.return_value = mock_sse_transport
            
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session_cls.return_value = mock_session
            
            self.client.servers_config = {
                "explicit_http": {
                    "type": "http",
                    "url": "http://localhost:9000/sse"
                }
            }
            
            await self.client.connect_server("explicit_http")
            
            mock_sse_client.assert_called_with("http://localhost:9000/sse")
            
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
