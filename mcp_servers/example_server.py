import asyncio
import os.path
from typing import Literal

from agent.mcp_servers import MCPServerStack
from mcp_servers.wrapper import MCPServerWrapper


async def main(transport: Literal["stdio", "sse"] = "stdio"):
    servers = MCPServerWrapper(name="Demo", wrapped_servers=MCPServerStack.from_config(os.path.join(os.path.dirname(__file__), 'no_mcps.json')))
    async with servers:
        mcp = await servers.get_server()

        @mcp.tool()
        def secret_computation(a: int, b: int) -> str:
            """Does some secret computation based on two numbers. It will return a single number that is the result of that computation"""
            return f'The result of the secret computation is {a + b + 42}'

        @mcp.tool()
        def get_current_weather() -> str:
            """Find out the current weather at your location. Returns the weather information as a descriptive text."""
            return f'The weather is sunny, with volcanic ashes in the sky.'

        # @mcp.resource("retrieve_user_id://{name}")
        # def retrieve_user_id(name: str) -> str:
        #     """Gets the user id from the name of the user"""
        #     return f"Hello, {name}!"

        mcp.settings.port = 16041
        if transport =='sse':
            await mcp.run_sse_async()
        else:
            await mcp.run_stdio_async()


if __name__ == '__main__':
    asyncio.run(main())
