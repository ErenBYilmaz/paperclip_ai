import asyncio
import os
import unittest

import mcp_servers
from frontend_v3 import Chat
from mcp_servers.server_stack import MCPServerStack
from mcp_servers.wrapper import MCPServerWrapper
from test.resources import example_savegame_8_clips


class TestTools(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.servers = MCPServerWrapper(name="Test", wrapped_servers=MCPServerStack.from_config(os.path.join(os.path.dirname(mcp_servers.__file__), 'wrapped_mcps.json')))
        self.no_servers = MCPServerWrapper(name="Test", wrapped_servers=MCPServerStack.from_config(os.path.join(os.path.dirname(mcp_servers.__file__), 'no_mcps.json')))

    async def test_playwright_tools_available(self):
        async with self.servers:
            tools_by_name = await self.servers.tool_dict()
            assert any(tool_name.lower().startswith('playwright') for tool_name in tools_by_name), "No playwright tools available"
            del tools_by_name
        await asyncio.sleep(0.5)

    async def test_tool_info_available(self):
        async with self.servers:
            tools_by_name = await self.servers.tool_dict()
            tool = tools_by_name['playwright_navigate']
            assert tool.function.name == 'playwright_navigate'
            assert 'URL' in tool.function.description
            assert 'url' in tool.function.parameters.properties
            assert 'URL' in tool.function.parameters.properties['url'].description

    async def test_navigate_and_save_pdf(self):
        assert os.environ['DISPLAY'] == 'host.docker.internal:0.0', os.environ['DISPLAY']
        async with self.servers:
            server = await self.servers.wrapped_servers.server_by_tool('playwright_navigate')
            print(await server.call_tool('playwright_navigate', {"url": "https://www.example.com", "browserType": "chromium"}))
            print(await server.call_tool('playwright_save_as_pdf', {"outputPath": "/code/screenshots", "filename": "test.pdf", "browserType": 'chromium'}))
            await asyncio.sleep(2)
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
            await asyncio.sleep(2)
        await asyncio.sleep(1)

    async def test_grabbing_example_html(self):
        prompt = 'Hello. Get the visible html of the currently opened page in playwright using the tool "playwright_get_visible_html". Then open "example.com" using "playwright_navigate" and grab the html from there as well.'
        async with self.servers:
            chat = await Chat.create(self.servers, model_name='mistral-nemo')
            chat.add_system_message('You are a helpful assistant that can use tools to interact with the web. '
                                    'You dont provide code, but instead use the chat history and the provided tools to get the information you need. '
                                    'You can do simple math, but you are not a calculator. ')
            response = chat.get_next_response(prompt)
            await chat.process_response(response)
            self.assertIsNotNone(response.message.tool_calls)
            assert len(response.message.tool_calls) > 0
            response = chat.get_next_response('What is the background color of the body of the page we just looked at?')
            await chat.process_response(response)
            if '#f0f0f2' not in response.message.content:
                response = chat.get_next_response(None)  # continue the conversation without a new prompt, but with the tool output
            await chat.process_response(response)
            self.assertIn('#f0f0f2', response.message.content)
            await asyncio.sleep(1)
        await asyncio.sleep(1)

    async def test_model_can_access_previous_messages(self):
        async with self.no_servers:
            chat = await Chat.create(self.no_servers)
            response = chat.get_next_response('What is 7 + 4?')
            await chat.process_response(response)
            self.assertIn('11', response.message.content)
            response = chat.get_next_response('And if you add another 4?')
            await chat.process_response(response)
            self.assertIn('11', response.message.content)
        await asyncio.sleep(1)
