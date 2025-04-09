import asyncio
import os

import ollama

from mcp_servers.server_stack import MCPServerStack
from mcp_servers.wrapper import MCPServerWrapper


async def main():
    prompt = 'Get the visible html of the currently opened page in playwright using the tool "playwright_get_visible_html". Then open "example.com" using "playwright_navigate" and grab the html from there as well.'
    servers = MCPServerWrapper(name="Demo", wrapped_servers=MCPServerStack.from_config(os.path.join(os.path.dirname(__file__), 'mcp_servers', 'wrapped_mcps.json')))
    async with servers:
        tools_by_name = await servers.tool_dict()
        tools = list(tools_by_name.values())
        print('Tools:', list(tools_by_name))

        client = ollama.Client(
            host='host.docker.internal'
        )
        response = client.chat(
            'llama3.2',
            messages=[{'role': 'user', 'content': prompt}],
            tools=tools
        )
        print(response.message.content)
        if response.message.tool_calls:
            for tool in response.message.tool_calls:
                if tool.function.name not in tools_by_name:
                    raise ValueError(f"Tool {tool.function.name} not found")
                tool_function = tools_by_name[tool.function.name]
                arguments = tool.function.arguments
                print('Calling tool:', tool.function.name, 'with arguments:', arguments)
                tool_response = await tool_function(**arguments)
                print('Tool response:', tool_response)
                await asyncio.sleep(1)
        await asyncio.sleep(0.5)
    await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.run(main())
