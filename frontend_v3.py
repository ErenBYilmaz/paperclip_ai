import asyncio
import os

import ollama

from mcp_servers.server_stack import MCPServerStack
from mcp_servers.wrapper import MCPServerWrapper


class Chat:
    def __init__(self, client: ollama.Client, tools: dict):
        self.client = client
        self.tools = tools

    @staticmethod
    async def create(servers: MCPServerWrapper):
        client =  ollama.Client(host='host.docker.internal')
        tools_by_name = await servers.tool_dict()
        return Chat(client=client, tools=tools_by_name)

    def tools_list(self):
        return list(self.tools.values())


async def main():
    prompt = 'Get the visible html of the currently opened page in playwright using the tool "playwright_get_visible_html". Then open "example.com" using "playwright_navigate" and grab the html from there as well.'
    servers = MCPServerWrapper(name="Demo", wrapped_servers=MCPServerStack.from_config(os.path.join(os.path.dirname(__file__), 'mcp_servers', 'wrapped_mcps.json')))
    async with servers:
        chat = await Chat.create(servers)
        response = chat.client.chat(
            'llama3.2',
            messages=[{'role': 'user', 'content': prompt}],
            tools=chat.tools_list()
        )
        print('Chat message received:', response.message.content)
        if response.message.tool_calls:
            for tool in response.message.tool_calls:
                if tool.function.name not in chat.tools:
                    raise ValueError(f"Tool {tool.function.name} not found")
                tool_function = chat.tools[tool.function.name]
                arguments = tool.function.arguments
                print('Calling tool:', tool.function.name, 'with arguments:', arguments)
                tool_response = await tool_function(**arguments)
                print('Tool response:', tool_response)
                await asyncio.sleep(1)

async def give_time_for_cleanup(fn, sleep_time=0.5):
    await fn
    await asyncio.sleep(sleep_time)

if __name__ == '__main__':
    asyncio.run(give_time_for_cleanup(main()))
