import asyncio
import json
import os.path
from typing import List, Union, Dict

import ollama
from agents.mcp import MCPServerStdio, MCPServerSse


def mcp_server_from_config(config: Union[dict, str], name):
    if isinstance(config, str):
        with open(config, 'r') as f:
            config = json.load(f)
    if "command" in config:
        server = MCPServerStdio(params=config, name=name)
    elif "url" in config:
        server = MCPServerSse(params=config, name=name)
    else:
        raise ValueError(f"Unknown MCP server configuration: {name}")
    return server


class MCPServerStack:
    def __init__(self, mcp_servers: List[MCPServerSse | MCPServerStdio]):
        self.mcp_servers = mcp_servers
        self._tools_on_servers_cached = None

    async def __aenter__(self):
        for server in self.mcp_servers:
            await server.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for server in self.mcp_servers:
            await server.__aexit__(exc_type, exc_val, exc_tb)

    async def connect(self):
        for server in self.mcp_servers:
            await server.connect()

    async def list_available_mcp_tools(self):
        """
        Create a list of MCPServer objects from the given configuration.
        """
        all_tools = []
        for server in self.mcp_servers:
            tools = await server.list_tools()
            all_tools.extend(tools)
        return all_tools

    async def tools_by_servers(self) -> Dict[str, List[str]]:
        if self._tools_on_servers_cached is None:
            result = {}
            for server in self.mcp_servers:
                server_name = server.name
                tools = await server.list_tools()
                result[server_name] = [tool.name for tool in tools]
            self._tools_on_servers_cached = result
        return self._tools_on_servers_cached

    @staticmethod
    def from_config(mcp_config_or_path=None):
        mcp_config = MCPServerStack.get_config(mcp_config_or_path)
        mcp_servers = []
        for name, config in mcp_config['mcpServers'].items():
            server = mcp_server_from_config(config, name)
            mcp_servers.append(server)
        stack = MCPServerStack(mcp_servers)
        return stack

    @staticmethod
    def get_config(mcp_config_or_path):
        if isinstance(mcp_config_or_path, dict):
            return mcp_config_or_path
        if isinstance(mcp_config_or_path, str):
            mcp_config_path = mcp_config_or_path
        elif mcp_config_or_path is None:
            mcp_config_path = os.path.join(os.path.dirname(__file__), 'mcp.json')
        else:
            raise ValueError
        with open(mcp_config_path, 'r') as f:
            mcp_config = json.load(f)
        return mcp_config

    async def call_tool(self, server, tool_name, arguments):
        return await server.call_tool(tool_name, arguments)

    async def server_by_tool(self, tool_name):
        tools_by_servers = await self.tools_by_servers()
        servers = [server for server in self.mcp_servers
                   if tool_name in tools_by_servers[server.name]]
        assert len(servers) == 1
        server = servers[0]
        return server

    async def tool_dict(self) -> Dict[str, ollama.Tool]:
        tools = await self.list_available_mcp_tools()
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


def main():
    servers = MCPServerStack.from_config()
    async def ls():
        async with servers:
            result = await servers.list_available_mcp_tools()
        await asyncio.sleep(0.5)
        return result
    asyncio.run(ls())


if __name__ == '__main__':
    main()
