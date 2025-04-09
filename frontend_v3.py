import ollama

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

    def get_next_response(self, prompt):
        return self.client.chat(
            'llama3.2',
            messages=[{'role': 'user', 'content': prompt}],
            tools=self.tools_list()
        )

    async def process_response(self, response):
        print('Chat message received:', response.message.content)
        if response.message.tool_calls:
            for tool in response.message.tool_calls:
                if tool.function.name not in self.tools:
                    raise ValueError(f"Tool {tool.function.name} not found")
                tool_function = self.tools[tool.function.name]
                arguments = tool.function.arguments
                print('Calling tool:', tool.function.name, 'with arguments:', arguments)
                tool_response = await tool_function(**arguments)
                print('Tool response:', tool_response)
