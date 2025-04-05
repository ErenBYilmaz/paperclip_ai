import asyncio
import os
import unittest

from agent.paperclip_agent import Agent


class TestTools(unittest.TestCase):
    def test_playwright_tools_available(self):
        a = Agent()
        tools = a.tools()
        assert any(tool.name.lower().startswith('playwright') for tool in tools), "No playwright tools available"

    def test_navigate(self):
        print()
        print(os.environ['DISPLAY'])
        assert os.environ['DISPLAY'] == 'host.docker.internal:0.0'
        a = Agent()
        servers = a.mcp_server_stack.mcp_servers
        print([server.name for server in servers])
        servers = [server for server in servers if server.name == "playwright"]
        assert len(servers) == 1
        server = servers[0]

        async def call():
            async with server:
                await server.call_tool('playwright_navigate', {"url": "https://www.example.com"})
                await asyncio.sleep(10)
            await asyncio.sleep(1)

        asyncio.run(call())
