import asyncio
import time
import unittest

from agent.paperclip_agent import Agent


class TestTools(unittest.TestCase):
    def test_puppeteer_tools_available(self):
        a = Agent()
        tools = a.tools()
        assert any(tool.name.startswith('puppeteer') for tool in tools), "No puppeteer tools available"

    def test_navigate(self):
        a = Agent()
        servers = a.mcp_server_stack.mcp_servers
        print([server.name for server in servers])
        servers = [server for server in servers if server.name == "puppeteer"]
        assert len(servers) == 1
        server = servers[0]

        async def call():
            async with server:
                await server.call_tool('puppeteer_navigate', {"url": "https://www.example.com"})

        asyncio.run(call())
        time.sleep(10)
