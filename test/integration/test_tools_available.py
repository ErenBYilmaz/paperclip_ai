import asyncio
import os
import unittest

import mcp_servers
from callback import RemoveInvisibleHTML
from frontend_v3 import Chat, create_tool_call_object
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

    async def test_automatically_grabbing_example_html(self):
        # prompt = 'Get the background color of the body at example.com. You will probably find it in the visible html when you have navigated to that page.'
        prompt = ('Hello. Get the visible html of the currently opened page in playwright using the tool "playwright_get_visible_html". '
                  'Then open "example.com" using "playwright_navigate" and grab the html from there. '
                  'Check if you find the background color of the body in the html and report back to me.')

        async with self.servers:
            chat = await Chat.create(self.servers, model_name='mistral-nemo')
            chat.add_system_message('You are a helpful assistant that can use tools to interact with the web. '
                                    'You use the chat history and the provided tools to get the information you need.')
            await chat.interaction(prompt)
            last_message = chat.messages[-1]
            self.assertIn('#f0f0f2', last_message.content)
            await asyncio.sleep(1)
        await asyncio.sleep(1)

    async def test_automation_without_naming_tools(self):
        prompt = ('Hello. '
                  'Use playwright to navigate to "example.com" and grab the html from there as well. '
                  'Check if you find the background color of the body of example.com in the html and report back to me.')

        async with self.servers:
            chat = await Chat.create(self.servers, model_name='qwen2.5-coder')
            chat.remove_tools([t.function.name for t in chat.tools_list()
                               if 'codegen' in t.function.name
                               or 'assert' in t.function.name
                               or 'expect' in t.function.name]
                              + ['playwright_get', 'playwright_post', 'playwright_put', 'playwright_delete', 'playwright_patch', 'playwright_evaluate'])
            chat.print_tools()
            await chat.interaction(prompt)
            last_message = chat.messages[-1]
            print(chat.history_str())
            self.assertIn('#f0f0f2', last_message.content)
            await asyncio.sleep(1)
        await asyncio.sleep(1)

    async def test_making_a_few_paperclips(self):
        prompt = ('Hello. We are playing the browsergame "Universal Paperclips"! '
                  'I have already opened the web browser for you and collected the html contents. '
                  'Get the visible html and click the paperclip-making button. '
                  'Then check the new html of the page and report how many paperclips we have available now.')

        async with self.servers:
            chat = await Chat.create(self.servers, model_name='mistral-nemo')
            await chat.call_tool_and_add_output_message(create_tool_call_object(name='playwright_navigate', arguments={"url": "https://www.decisionproblem.com/paperclips/index2.html", "browserType": "chromium"}))
            await chat.call_tool_and_add_output_message(create_tool_call_object(name='playwright_get_visible_html', arguments={}))
            javascript_call_for_restoring_savegame = f's = JSON.parse({example_savegame_8_clips});' + 'for (const key in s){localStorage.setItem(key, s[key])};load()'
            await chat.call_tool_and_add_output_message(create_tool_call_object(name='playwright_evaluate', arguments={"script": javascript_call_for_restoring_savegame}))
            chat.remove_tools([t.function.name for t in chat.tools_list()
                               if 'codegen' in t.function.name
                               or 'assert' in t.function.name
                               or 'expect' in t.function.name]
                              + ['playwright_get', 'playwright_post', 'playwright_put', 'playwright_delete', 'playwright_patch', 'playwright_evaluate'])
            chat.callbacks.append(RemoveInvisibleHTML())
            chat.messages.clear()
            chat.print_tools()
            await chat.interaction(prompt)
            print(chat.history_str())
            last_message = chat.messages[-1]
            self.assertIn('9', last_message.content)
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
