import asyncio
import functools

from mcp.server import FastMCP

from agent.mcp_servers import MCPServerStack


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

    def wrapped_tool_call(self, tool_name):
        @functools.wraps(self.wrapped_servers.call_tool)
        def wrapper(arguments):
            return asyncio.run(self.wrapped_servers.call_tool(tool_name, arguments))

        return wrapper

    def get_server(self) -> FastMCP:
        tools = asyncio.run(self.wrapped_servers.list_available_mcp_tools())
        result = FastMCP(self.name)
        result.settings.port = self.port
        result.settings.host = self.host
        for tool in tools:
            result.add_tool(self.wrapped_tool_call(tool.name), tool.name, tool.description)
            added_tool = result._tool_manager.get_tool(tool.name)
            assert added_tool.name == tool.name
            added_tool.parameters = tool.inputSchema
            added_tool.parameters['title'] = f'{tool.name}Arguments'
        return result
