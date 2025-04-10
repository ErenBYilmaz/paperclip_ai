import os
from typing import List, Dict, Callable, Optional

import ollama
from mcp.types import CallToolResult, TextContent
from ollama import Message

from mcp_servers.wrapper import MCPServerWrapper


class ChatCallback:
    async def after_tool_call(self, chat: 'Chat', tool: ollama.Message.ToolCall, tool_response):
        raise NotImplementedError('Abstract method')


class AfterToolCallAnotherTool(ChatCallback):
    def __init__(self, first_tool_name: str, other_tool_call: ollama.Message.ToolCall):
        self.first_tool_name = first_tool_name
        self.other_tool_call = other_tool_call

    async def after_tool_call(self, chat: 'Chat', tool: ollama.Message.ToolCall, tool_response):
        if tool.function.name == self.first_tool_name:
            await chat.call_tool_and_add_output_message(self.other_tool_call)


class Chat:
    def __init__(self, client: ollama.Client, tools: Dict[str, ollama.Tool], tool_callables: Dict[str, Callable], model_name='llama3.2', callbacks: List[ChatCallback] = None):
        if callbacks is None:
            callbacks = []
        self.callbacks = callbacks
        self.client = client
        self.tools = tools
        self.model_name = model_name
        self.tool_callables = tool_callables
        self.messages: List[ollama.Message] = []
        for tool_name, tool in tools.items():
            assert tool_name == tool.function.name, f"Tool name mismatch: {tool_name} != {tool.name}"

    @staticmethod
    async def create(servers: MCPServerWrapper, model_name='llama3.2'):
        client = ollama.Client(host='host.docker.internal')
        tools_by_name = await servers.tool_dict()
        tool_callables = await servers.tool_callables()
        return Chat(client=client, tools=tools_by_name, tool_callables=tool_callables, model_name=model_name)

    def tools_list(self) -> List[ollama.Tool]:
        return list(self.tools.values())

    def add_system_message(self, prompt):
        self.messages.append(Message(role='system', content=prompt))
        print('System message added:', prompt)

    def add_tools_system_message(self):
        self.add_system_message(prompt=(self.tools_description()))

    def tools_description(self):
        tools_description = 'You have the following tools available:\n'
        for tool_name, tool in self.tools.items():
            tools_description += f"- {tool_name}: {tool.function.description}\n"
            tools_description += f'  -> {tool_name} arguments: {tool.function.parameters.model_dump_json()}\n'
        return tools_description

    def get_next_response(self, prompt: Optional[str]):
        if prompt is None:
            print('Asking for model output...')
        else:
            print('Sending prompt:', prompt)
            self.messages.append(ollama.Message(role='user', content=prompt))
        return self.client.chat(
            self.model_name,
            messages=self.messages,
            tools=self.tools_list(),
            options=ollama.Options(temperature=0)
        )

    async def interaction(self, prompt: str, auto_send_back_tool_results=True, max_steps=10):
        response = self.get_next_response(prompt)
        await self.process_response(response)
        steps = 0
        if auto_send_back_tool_results:
            while response.message.tool_calls and len(response.message.tool_calls) > 0:
                if os.path.isfile('stop.dat'):
                    break
                response = self.get_next_response(None)
                await self.process_response(response)
                steps += 1
                if steps > max_steps:
                    print('Max steps reached, stopping interaction.')
                    break

    def history_str(self):
        history = ''
        for step, message in enumerate(self.messages):
            if message.content.strip() != '':
                lines = message.content.strip().splitlines()
                if len(lines) <= 3:
                    content = '\n'.join(lines)
                else:
                    content = '\n'.join(lines[:3]) + '[...]'
                history += f'{step + 1: 3d}. {message.role}: {content}\n'
            if message.tool_calls is not None and len(message.tool_calls) > 0:
                history += f'{step + 1: 3d}. Tool calls:\n'
                for tool_call in message.tool_calls:
                    history += f'    - {tool_call.function.name}({tool_call.function.arguments})\n'
        return history

    async def process_response(self, response: ollama.ChatResponse):
        print('Chat message received:', response.message.content)
        self.messages.append(response.message)
        any_tool_missing = False
        if response.message.tool_calls:
            for tool in response.message.tool_calls:
                if tool.function.name not in self.tools:
                    print('Tool not found:', tool.function.name)
                    self.messages.append(Message(role='tool', content=f"Tool {tool.function.name} not available."))
                    any_tool_missing = True
                    continue
                await self.call_tool_and_add_output_message(tool)
        if any_tool_missing:
            self.messages.append(Message(role='tool', content=f'Reminder: you only have the following tools available: {list(self.tools.keys())}'))

    async def call_tool_and_add_output_message(self, tool: ollama.Message.ToolCall):
        tool_function = self.tool_callables[tool.function.name]
        arguments = tool.function.arguments
        print('Calling tool:', tool.function.name, 'with arguments:', arguments)
        tool_response = await tool_function(**arguments)
        print('Tool response:', tool_response)
        self.messages.append(Message(role='tool', content=f'{tool.function.name}:\n{self.tool_response_to_text(tool_response)}'))
        await self.after_tool_call(tool, tool_response)

    async def after_tool_call(self, tool: ollama.Message.ToolCall, tool_response):
        for c in self.callbacks:
            await c.after_tool_call(self, tool, tool_response)

    def print_tools(self):
        print(self.tools_description())

    def remove_tools(self, tool_names: List[str]):
        for tool_name in tool_names:
            del self.tool_callables[tool_name]
            del self.tools[tool_name]

    def tool_response_to_text(self, tool_response) -> str:
        if isinstance(tool_response, CallToolResult):
            for response_content in tool_response.content:
                if isinstance(response_content, TextContent):
                    t = response_content.text
                    if response_content.annotations is not None:
                        raise NotImplementedError('TO DO')
                    return t
                else:
                    raise NotImplementedError(f'TO DO: Implement processing {type(response_content)}')
        elif isinstance(tool_response, (int, float, bool)):
            return str(tool_response)
        elif isinstance(tool_response, str):
            return tool_response
        else:
            raise NotImplementedError(f'TO DO: Implement processing {type(tool_response)}')
