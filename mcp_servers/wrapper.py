import asyncio
import functools
from typing import Dict, Callable

import ollama
from mcp.server import FastMCP
from mcp.server.fastmcp.utilities.func_metadata import FuncMetadata

from mcp_servers.json_schema_to_pydantic_model import json_schema_to_base_model
from mcp_servers.server_stack import MCPServerStack


def synchronize(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


class MCPServerWrapper:
    def __init__(self, wrapped_servers: MCPServerStack, name: str, host: str = "0.0.0.0", port: int = 8080):
        self.wrapped_servers = wrapped_servers
        self.name = name
        self.host = host
        self.port = port

    async def __aenter__(self):
        await self.wrapped_servers.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.wrapped_servers.__aexit__(exc_type, exc_val, exc_tb)

    def wrapped_tool_call(self, tool_name, server):
        # @functools.wraps(self.wrapped_servers.call_tool)
        async def wrapper(**arguments):
            return await self.wrapped_servers.call_tool(tool_name=tool_name,
                                                        server=server,
                                                        arguments=arguments)

        return wrapper

    async def get_server(self) -> FastMCP:
        tools = await self.wrapped_servers.list_available_mcp_tools()
        result = FastMCP(self.name)
        result.settings.port = self.port
        result.settings.host = self.host
        for tool in tools:
            server = await self.wrapped_servers.server_by_tool(tool.name)
            result.add_tool(self.wrapped_tool_call(tool.name, server=server), tool.name, tool.description)
            added_tool = result._tool_manager.get_tool(tool.name)
            assert added_tool.name == tool.name
            added_tool.parameters = tool.inputSchema
            added_tool.parameters['title'] = f'{tool.name}Arguments'
            arguments_model = json_schema_to_base_model(tool.inputSchema)
            # schema.model_config['arbitrary_types_allowed'] = True
            added_tool.fn_metadata = FuncMetadata(arg_model=arguments_model)
        return result

    async def tool_dict(self) -> Dict[str, ollama.Tool]:
        tools = await self.wrapped_servers.list_available_mcp_tools()
        result = {}
        for tool in tools:
            result[tool.name] = ollama.Tool(
                function=ollama.Tool.Function(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.inputSchema,
                )
            )
        return result

    async def tool_callables(self) -> Dict[str, Callable]:
        tools = await self.wrapped_servers.list_available_mcp_tools()
        result = {}
        for tool in tools:
            server = await self.wrapped_servers.server_by_tool(tool.name)
            result[tool.name] = self.wrapped_tool_call(tool.name, server=server)
        return result