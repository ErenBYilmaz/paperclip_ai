import asyncio
import os
import unittest

import mcp_servers
from callback import RemoveInvisibleHTML
from chat_message import create_tool_call_object
from frontend_v3 import OpenAIChat
from mcp_servers.server_stack import MCPServerStack
from mcp_servers.wrapper import MCPServerWrapper
from test.resources import example_savegame_8_clips


class TestTools(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.servers = MCPServerWrapper(name="Test", wrapped_servers=MCPServerStack.from_config(os.path.join(os.path.dirname(mcp_servers.__file__), 'wrapped_mcps.json')))
        self.no_servers = MCPServerWrapper(name="Test", wrapped_servers=MCPServerStack.from_config(os.path.join(os.path.dirname(mcp_servers.__file__), 'no_mcps.json')))

    async def test_models_available(self):
        chat = await OpenAIChat.create(self.no_servers, model_name='o1-mini')
        models = [model.id for model in chat.client.models.list()]
        print(models)
        assert len(models) > 0

    async def test_making_a_paperclip(self):
        prompt = ('Hello. We are playing the browsergame "Universal Paperclips"! '
                  'I have already opened the web browser for you and collected the html contents. '
                  'Get the visible html and click the paperclip-making button. '
                  'Then check the new html of the page and report how many paperclips we have available now.')

        async with self.servers:
            chat = await OpenAIChat.create(self.servers, model_name='o3-mini')
            chat.callbacks.append(RemoveInvisibleHTML())
            await chat.call_tool_and_add_output_message(
                create_tool_call_object(name='playwright_navigate', arguments={"url": "https://www.decisionproblem.com/paperclips/index2.html", "browserType": "chromium"}))
            await chat.call_tool_and_add_output_message(create_tool_call_object(name='playwright_get_visible_html', arguments={}))
            javascript_call_for_restoring_savegame = f's = JSON.parse({example_savegame_8_clips});' + 'for (const key in s){localStorage.setItem(key, s[key])};load()'
            await chat.call_tool_and_add_output_message(create_tool_call_object(name='playwright_evaluate', arguments={"script": javascript_call_for_restoring_savegame}))
            chat.remove_tools([t.function.name for t in chat.tools_list()
                               if 'codegen' in t.function.name
                               or 'assert' in t.function.name
                               or 'expect' in t.function.name]
                              + ['playwright_get', 'playwright_post', 'playwright_put', 'playwright_delete', 'playwright_patch', 'playwright_evaluate'])
            chat.messages.clear()
            chat.print_tools()
            await chat.interaction(prompt)
            print(chat.history_str())
            last_message = chat.messages[-1]
            self.assertIn('9', last_message.content)
            await asyncio.sleep(1)
        await asyncio.sleep(1)

