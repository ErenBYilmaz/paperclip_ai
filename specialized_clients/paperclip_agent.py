import json
import os
from typing import Optional

import mcp_servers
from callback import RemoveInvisibleHTML
from chat_message import create_tool_call_object
from frontend_v3 import OpenAIChat, Chat, OllamaChat
from mcp_servers.server_stack import MCPServerStack
from mcp_servers.wrapper import MCPServerWrapper
from test.resources import example_savegame_8_clips


class PaperclipAgent:
    def __init__(self, model_name=None):
        if model_name is None:
            model_name = self.default_model_name()
        self.servers = MCPServerWrapper(name="Test", wrapped_servers=MCPServerStack.from_config(os.path.join(os.path.dirname(mcp_servers.__file__), 'wrapped_mcps.json')))
        self.chat: Optional[Chat] = None
        self.model_name = model_name

    def default_model_name(self):
        raise NotImplementedError('abstract method')

    async def __aenter__(self):
        await self.servers.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.servers.__aexit__(exc_type, exc_val, exc_tb)

    def initial_prompt(self):
        return (
            'Hello. We are playing the browsergame "Universal Paperclips"!\n'
            'I have already opened the web browser for you and you can have a look by collecting the html contents.\n'
            'You are now in charge of the game: Try to make as many paperclips as possible.\n'
            'I have put you in a testing scenario where you can\'t really break things, so feel free to experiment and try to find out how the game works.\n'
        )

    async def run(self):
        if self.chat is None:
            raise RuntimeError('Chat not initialized. Call setup() first.')
        await self.chat.interaction(self.initial_prompt())

    async def setup(self, save_path=None):
        self.chat = await self.create_chat()
        self.chat.callbacks.append(RemoveInvisibleHTML())
        await self.chat.call_tool_and_add_output_message(
            create_tool_call_object(name='playwright_navigate', arguments={"url": "https://www.decisionproblem.com/paperclips/index2.html", "browserType": "chromium"}))
        await self.chat.call_tool_and_add_output_message(create_tool_call_object(name='playwright_get_visible_html', arguments={}))
        if save_path is not None:
            await self.restore_game(save_path)
        self.chat.remove_tools([t.function.name for t in self.chat.tools_list()
                                if 'codegen' in t.function.name
                                or 'assert' in t.function.name
                                or 'expect' in t.function.name]
                               + ['playwright_get', 'playwright_post', 'playwright_put', 'playwright_delete', 'playwright_patch'])
        self.chat.messages.clear()
        self.chat.print_tools()

    async def restore_game(self, save_path):
        javascript_call_for_restoring_savegame = f's = JSON.parse({json.dumps(self.load_game(save_path))});' + 'for (const key in s){localStorage.setItem(key, s[key])};load()'
        await self.chat.call_tool_and_add_output_message(create_tool_call_object(name='playwright_evaluate', arguments={"script": javascript_call_for_restoring_savegame}))

    async def create_chat(self):
        raise NotImplementedError('abstract method')

    def load_game(self, save_path: str) -> str:
        if save_path is None:
            return example_savegame_8_clips
        if not os.path.isfile(save_path):
            return example_savegame_8_clips
        with open(save_path, 'r') as f:
            json_dumped_save = f.read()
            return json_dumped_save

    async def save_game(self, state_json: str, save_path: str):
        with open(save_path, 'w') as f:
            f.write(state_json)

    async def get_game_state_json(self) -> str:
        javascript_call_for_logging_savegame = "save();JSON.stringify(localStorage)"
        response = await self.chat.call_tool(create_tool_call_object(name='playwright_evaluate', arguments={"script": javascript_call_for_logging_savegame}))
        return json.loads(response.content[-1].text)


class OllamaPaperclipAgent(PaperclipAgent):
    async def create_chat(self):
        return await OllamaChat.create(self.servers, model_name=self.model_name)

    def default_model_name(self):
        return 'mistral-nemo'


class OpenAIPaperclipAgent(PaperclipAgent):
    async def create_chat(self):
        return await OpenAIChat.create(self.servers, model_name=self.model_name)

    def default_model_name(self):
        return 'o3-mini'
