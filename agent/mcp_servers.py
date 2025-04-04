import asyncio
import json
import os.path

from agents.mcp import MCPServerStdio, MCPServerSse


class MCPServerStack:
    def __init__(self, mcp_servers):
        self.mcp_servers = mcp_servers

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

    @staticmethod
    def from_config(mcp_config=None):
        if mcp_config is None:
            mcp_config_path = os.path.join(os.path.dirname(__file__), 'mcp.json')
            with open(mcp_config_path, 'r') as f:
                mcp_config = json.load(f)
        mcp_servers = []
        for name, config in mcp_config['mcpServers'].items():
            if "command" in config:
                mcp_servers.append(MCPServerStdio(params=config))
            elif "url" in config:
                mcp_servers.append(MCPServerSse(params=config))
            else:
                raise ValueError(f"Unknown MCP server configuration: {name}")
        stack = MCPServerStack(mcp_servers)
        return stack


def main():
    asyncio.run(MCPServerStack.from_config().list_available_mcp_tools())


if __name__ == '__main__':
    main()
