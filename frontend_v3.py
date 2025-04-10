import os
from typing import List, Dict, Callable, Optional

import ollama
from mcp.types import CallToolResult, TextContent
from ollama import Message

from mcp_servers.wrapper import MCPServerWrapper


class Chat:
    def __init__(self, client: ollama.Client, tools: Dict[str, ollama.Tool], tool_callables: Dict[str, Callable], model_name='llama3.2'):
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
        tools_description = 'You have the following tools available:\n'
        for tool_name, tool in self.tools.items():
            tools_description += f"- {tool_name}: {tool.function.description}\n"
            tools_description += f'  -> {tool_name} arguments: {tool.function.parameters.model_dump_json()}\n'
        self.add_system_message(prompt=tools_description)

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

    async def interaction(self, prompt: str, auto_send_back_tool_results=True):
        response = self.get_next_response(prompt)
        await self.process_response(response)
        if auto_send_back_tool_results:
            while response.message.tool_calls and len(response.message.tool_calls) > 0:
                if os.path.isfile('stop.dat'):
                    break
                response = self.get_next_response(None)
                await self.process_response(response)

    async def process_response(self, response: ollama.ChatResponse):
        print('Chat message received:', response.message.content)
        self.messages.append(response.message)
        if response.message.tool_calls:
            for tool in response.message.tool_calls:
                if tool.function.name not in self.tools:
                    print('Tool not found:', tool.function.name)
                    self.messages.append(Message(role='tool', content=f"Tool {tool.function.name} not found."))
                    continue
                tool_function = self.tool_callables[tool.function.name]
                arguments = tool.function.arguments
                print('Calling tool:', tool.function.name, 'with arguments:', arguments)
                tool_response = await tool_function(**arguments)
                print('Tool response:', tool_response)
                self.messages.append(Message(role='tool', content=self.tool_response_to_text(tool_response)))

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
