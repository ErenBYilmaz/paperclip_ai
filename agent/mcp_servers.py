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


async def mcp_servers_from_config(mcp_config):
    """
    Create a list of MCPServer objects from the given configuration.
    """
    mcp_servers = []
    for name, config in mcp_config['mcpServers'].items():
        if "command" in config:
            mcp_servers.append(MCPServerStdio(params=config))
        elif "url" in config:
            mcp_servers.append(MCPServerSse(params=config))
        else:
            raise ValueError(f"Unknown MCP server configuration: {name}")
    for server in mcp_servers:
        async with server:
            tools = await server.list_tools()
            for tool in tools:
                print(tool)
        await asyncio.sleep(0.2)
    return mcp_servers


def main():
    with open(os.path.join(os.path.dirname(__file__), 'mcp.json'), 'r') as f:
        mcp_config = json.load(f)
    asyncio.run(mcp_servers_from_config(mcp_config))


if __name__ == '__main__':
    main()