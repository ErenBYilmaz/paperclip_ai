import asyncio
import json
import os.path
from typing import List, Union, Dict

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

    async def list_available_mcp_tools(self):
        """
        Create a list of MCPServer objects from the given configuration.
        """
        all_tools = []
        async with self:
            for server in self.mcp_servers:
                tools = await server.list_tools()
                for tool in tools:
                    print(tool)
                all_tools.extend(tools)
        await asyncio.sleep(0.2)
        return all_tools

    def tools_on_servers(self) -> Dict[str, List[str]]:
        if self._tools_on_servers_cached is None:
            result = {}
            for server in self.mcp_servers:
                server_name = server.name
                tools = asyncio.run(server.list_tools())
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

    async def call_tool(self, tool_name, arguments):
        servers = [server for server in self.mcp_servers
                   if tool_name in self.tools_on_servers()[server.name]]
        assert len(servers) == 1
        server = servers[0]
        await server.call_tool(tool_name, arguments)


def main():
    asyncio.run(MCPServerStack.from_config().list_available_mcp_tools())


if __name__ == '__main__':
    main()
