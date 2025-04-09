import asyncio
import os
import unittest

import mcp_servers
from mcp_servers.server_stack import MCPServerStack
from mcp_servers.wrapper import MCPServerWrapper
from test.resources import example_savegame_8_clips


class TestTools(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.servers = MCPServerWrapper(name="Test", wrapped_servers=MCPServerStack.from_config(os.path.join(os.path.dirname(mcp_servers.__file__), 'wrapped_mcps.json')))

    async def test_playwright_tools_available(self):
        async with self.servers:
            tools_by_name = await self.servers.tool_dict()
            assert any(tool_name.lower().startswith('playwright') for tool_name in tools_by_name), "No playwright tools available"
            del tools_by_name
        await asyncio.sleep(0.5)

    async def test_navigate_and_save_pdf(self):
        assert os.environ['DISPLAY'] == 'host.docker.internal:0.0', os.environ['DISPLAY']
        async with self.servers:
            server = await self.servers.wrapped_servers.server_by_tool('playwright_navigate')
            print(await server.call_tool('playwright_navigate', {"url": "https://www.example.com", "browserType": "chromium"}))
            print(await server.call_tool('playwright_save_as_pdf', {"outputPath": "/code/screenshots", "filename": "test.pdf", "browserType": 'chromium'}))
            print('Waiting 10 seconds for the server to process the request...')
            await asyncio.sleep(10)
        await asyncio.sleep(1)

    async def test_if_cookies_are_being_stored(self):
        assert os.environ['DISPLAY'] == 'host.docker.internal:0.0', os.environ['DISPLAY']
        async with self.servers:
            server = await self.servers.wrapped_servers.server_by_tool('playwright_navigate')

            print(await server.call_tool('playwright_navigate', {"url": "https://www.decisionproblem.com/paperclips/index2.html", "browserType": "chromium"}))
            json_dumped_save = example_savegame_8_clips
            javascript_call_for_restoring_savegame = f's = JSON.parse({json_dumped_save});' + 'for (const key in s){localStorage.setItem(key, s[key])};load()'
            print(javascript_call_for_restoring_savegame)
            print(await server.call_tool('playwright_evaluate', {"script": javascript_call_for_restoring_savegame}))
            print(await server.call_tool('playwright_click', {"selector": "#btnMakePaperclip"}))
            print(await server.call_tool('playwright_click', {"selector": "#btnMakePaperclip"}))
            print(await server.call_tool('playwright_click', {"selector": "#btnMakePaperclip"}))
            print(await server.call_tool('playwright_click', {"selector": "#btnMakePaperclip"}))
            print(await server.call_tool('playwright_evaluate', {"script": "save();JSON.stringify(localStorage)"}))
            html_response = await server.call_tool('playwright_get_visible_html', {})
            print(html_response)
            html_response = '\n'.join(html_response.content[0].text.splitlines()[1:])
            print(html_response)
            print('Waiting 10 seconds for the server to process the request...')
            await asyncio.sleep(10)
        await asyncio.sleep(1)
