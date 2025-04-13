import json
import os
import uuid
from typing import List, Dict, Callable, Optional, Literal

import ollama
import openai.types.responses
from mcp.types import CallToolResult, TextContent
from openai import OpenAI

from callback import ChatCallback
from chat_message import ChatMessage
from mcp_servers.wrapper import MCPServerWrapper


class Chat:
    def __init__(self, tools: Dict[str, ollama.Tool], tool_callables: Dict[str, Callable], callbacks: List[ChatCallback] = None):
        if callbacks is None:
            callbacks = []
        self.callbacks = callbacks
        self.tools = tools
        self.tool_callables = tool_callables
        self.messages: List[ChatMessage] = []
        for tool_name, tool in tools.items():
            assert tool_name == tool.function.name, f"Tool name mismatch: {tool_name} != {tool.name}"

    @staticmethod
    async def create(servers: MCPServerWrapper, model_name='llama3.2'):
        client = ollama.Client(host='host.docker.internal')
        tools_by_name = await servers.tool_dict()
        tool_callables = await servers.tool_callables()
        return OllamaChat(client=client, tools=tools_by_name, tool_callables=tool_callables, model_name=model_name)

    def tools_list(self) -> List[ollama.Tool]:
        return list(self.tools.values())

    def add_system_message(self, prompt):
        self.messages.append(ChatMessage(role='system', content=prompt))
        print('System message added:', prompt)

    def add_tools_system_message(self):
        self.add_system_message(prompt=(self.tools_description()))

    def tools_description(self):
        tools_description = 'You have the following tools available:\n'
        for tool_name, tool in self.tools.items():
            tools_description += f"- {tool_name}: {tool.function.description}\n"
            tools_description += f'  -> {tool_name} arguments: {tool.function.parameters.model_dump_json()}\n'
        return tools_description

    def get_next_response(self, prompt: Optional[str]) -> ChatMessage:
        if prompt is None:
            print('Asking for model output...')
        else:
            print('Sending prompt:', prompt)
            self.messages.append(ChatMessage(role='user', content=prompt))
        return self.api_call_for_model_response()

    def api_call_for_model_response(self) -> ChatMessage:
        raise NotImplementedError('Abstract method')

    async def interaction(self, prompt: str, auto_send_back_tool_results=True, max_steps=10):
        response = self.get_next_response(prompt)
        await self.process_response(response)
        steps = 0
        if auto_send_back_tool_results:
            while response.tool_calls and len(response.tool_calls) > 0:
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
                if len(lines) <= 5:
                    content = '\n'.join(lines)
                else:
                    content = '\n'.join(lines[:5]) + '[...]'
                history += f'{step + 1: 3d}. {message.role}: {content}\n'
            if message.tool_calls is not None and len(message.tool_calls) > 0:
                history += f'{step + 1: 3d}. Tool calls:\n'
                for tool_call in message.tool_calls:
                    history += f'    - {tool_call.function.name}({tool_call.function.arguments})\n'
        return history

    async def process_response(self, message: ChatMessage):
        print('Chat message received:', message.content)
        self.messages.append(message)
        missing_tools_for_calls = []
        if message.tool_calls:
            for tool in message.tool_calls:
                if tool.function.name not in self.tools:
                    print('Tool not found:', tool.function.name)
                    self.messages.append(ChatMessage(role='tool', content=f"Tool {tool.function.name} not available.", call_id=tool.call_id))
                    missing_tools_for_calls.append(tool.call_id)
                    continue
                await self.call_tool_and_add_output_message(tool)
        if len(missing_tools_for_calls) > 0:
            self.messages.append(ChatMessage(role='tool',
                                             content=f'Reminder: you only have the following tools available: {list(self.tools.keys())}',
                                             call_id=missing_tools_for_calls[-1]))

    async def call_tool_and_add_output_message(self, tool: ChatMessage.ToolCall):
        tool_function = self.tool_callables[tool.function.name]
        arguments = tool.function.arguments
        print('Calling tool:', tool.function.name, 'with arguments:', arguments)
        tool_response = await tool_function(**arguments)
        msg = ChatMessage(role='tool', content=f'{tool.function.name}:\n{self.tool_response_to_text(tool_response)}', call_id=tool.call_id)
        self.messages.append(msg)
        await self.after_tool_call(tool, tool_response)
        print('Tool response:', msg.content)

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


class OllamaChat(Chat):
    def __init__(self, client: ollama.Client, tools: Dict[str, ollama.Tool], tool_callables: Dict[str, Callable], model_name='llama3.2', callbacks: List[ChatCallback] = None):
        super().__init__(tools, tool_callables, callbacks)
        self.client = client
        self.model_name = model_name

    def add_call_ids(self, message: ollama.Message) -> ChatMessage:
        if message.tool_calls is None:
            calls = None
        else:
            calls = [ChatMessage.ToolCall(function=tool_call.function, call_id=self.generate_call_id(), ) for tool_call in message.tool_calls]
        return ChatMessage(
            role=message.role,
            content=message.content,
            images=message.images,
            tool_calls=calls
        )

    def generate_call_id(self):
        return str(uuid.uuid4())

    def api_call_for_model_response(self) -> ChatMessage:
        return self.add_call_ids(self.client.chat(
            self.model_name,
            messages=self.messages,
            tools=self.tools_list(),
            options=ollama.Options(temperature=0)
        ).message)


class OpenAIChat(Chat):
    def __init__(self, client: OpenAI, tools: Dict[str, ollama.Tool], tool_callables: Dict[str, Callable], model_name='llama3.2', callbacks: List[ChatCallback] = None):
        super().__init__(tools, tool_callables, callbacks)
        self.client = client
        self.model_name = model_name

    @staticmethod
    async def create(servers: MCPServerWrapper, model_name='gpt-4o'):
        client = OpenAI()
        tools_by_name = await servers.tool_dict()
        tool_callables = await servers.tool_callables()
        return OpenAIChat(client=client, tools=tools_by_name, tool_callables=tool_callables, model_name=model_name)

    def api_call_for_model_response(self) -> ChatMessage:
        response: openai.types.responses.Response = self.client.responses.create(
            model=self.model_name,
            input=self.formatted_input_messages(),
            tools=self.openai_formatted_tools(),
        )
        return self.message_from_openai_response(response)

    def openai_formatted_tools(self) -> List[openai.types.responses.FunctionToolParam]:
        tools = []
        for tool_name, tool in self.tools.items():
            tools.append(
                openai.types.responses.FunctionToolParam(
                    name=tool_name,
                    description=tool.function.description,
                    parameters=tool.function.parameters.model_dump(),
                    type="function",
                    strict=False,
                )
            )
        return tools

    def message_from_openai_response(self, response) -> ChatMessage:
        tool_calls: List[ollama.Message.ToolCall] = []
        for output in response.output:
            if output.type == "function_call":
                call: openai.types.responses.ResponseFunctionToolCall = output
                tool_calls.append(
                    ChatMessage.ToolCall(
                        function=ollama.Message.ToolCall.Function(
                            name=call.name,
                            arguments=json.loads(call.arguments),
                        ),
                        call_id=call.call_id,
                    )
                )
        return ChatMessage(
            role='assistant',
            content=response.output_text,
            tool_calls=tool_calls
        )

    def formatted_input_messages(self) -> openai.types.responses.ResponseInputParam:
        messages = []
        for m in self.messages:
            openai_message: openai.types.responses.ResponseInputItemParam
            if m.role == 'developer':
                raise NotImplementedError('TO DO')
            if m.role in ["user", "assistant", "system"]:
                role: Literal["user", "assistant", "system"] = m.role
                messages.append(openai.types.responses.EasyInputMessageParam(
                    content=m.content,
                    role=role,
                    type="message",
                ))
            elif m.role == 'tool':
                assert m.call_id is not None
                messages.append(openai.types.responses.response_input_item_param.FunctionCallOutput(
                    output=m.content,
                    call_id=m.call_id,
                    status="completed",
                    type='function_call_output'
                ))
            if m.tool_calls is not None:
                for t in m.tool_calls:
                    messages.append(openai.types.responses.response_function_tool_call_param.ResponseFunctionToolCallParam(
                        type="function_call",
                        status="completed",
                        call_id=t.call_id,
                        name=t.function.name,
                        arguments=json.dumps(t.function.arguments),
                    ))
        return messages
