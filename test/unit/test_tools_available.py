import asyncio
import os
import unittest

from agent.paperclip_agent import Agent


class TestTools(unittest.TestCase):
    def test_playwright_tools_available(self):
        a = Agent()
        tools = a.tools()
        assert any(tool.name.lower().startswith('playwright') for tool in tools), "No playwright tools available"

    def test_navigate_and_save_pdf(self):
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
                print(await server.call_tool('playwright_navigate', {"url": "https://www.example.com", "browserType": 'chromium'}))
                print(await server.call_tool('playwright_save_as_pdf', {"outputPath": "/code/", "filename": "test.pdf", "browserType": 'chromium'}))
                print('Waiting 10 seconds for the server to process the request...')
                await asyncio.sleep(10)
            await asyncio.sleep(1)

        asyncio.run(call())

    def test_if_cookies_are_being_stored(self):
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
                print(await server.call_tool('playwright_navigate', {"url": "https://www.decisionproblem.com/paperclips/index2.html", "browserType": 'chromium'}))
                print(await server.call_tool('playwright_click', {"selector": "#btnMakePaperclip"}))
                print(await server.call_tool('playwright_click', {"selector": "#btnMakePaperclip"}))
                print(await server.call_tool('playwright_click', {"selector": "#btnMakePaperclip"}))
                print(await server.call_tool('playwright_click', {"selector": "#btnMakePaperclip"}))
                print('Waiting 10 seconds for the server to process the request...')
                await asyncio.sleep(10)
            await asyncio.sleep(1)

        asyncio.run(call())
