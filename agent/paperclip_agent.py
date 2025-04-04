import asyncio
import json
import os

import agents
from agents import Runner

from agent.mcp_servers import MCPServerStack


def load_openai_environment_variables():
    for k in ['OPENAI_API_KEY', 'OPENAI_ORG_ID', 'OPENAI_PROJECT_ID']:
        if k not in os.environ:
            with open('/run/secrets/openai_config', 'r') as f:
                data = json.load(f)
                os.environ[k] = data[k]


class Agent:
    def __init__(self):
        load_openai_environment_variables()
        mcp_config_path = os.path.join(os.path.dirname(__file__), 'mcp.json')
        with open(mcp_config_path, 'r') as f:
            self.mcp_config = json.load(f)
        self.mcp_server_stack = MCPServerStack.from_config(self.mcp_config)
        self.openai_agent = agents.Agent(
            name='Assistant',
            instructions="You are a helpful assistant. You will be given a series of tasks to perform. ",
            mcp_servers=self.mcp_server_stack.mcp_servers
        )

    def run(self, prompt: str):
        print('Running agent with prompt:', prompt)
        return asyncio.run(self.arun(prompt))

    async def arun(self, prompt: str):
        print('Starting mcp servers...')
        async with self.mcp_server_stack:
            print('servers running')
            result = await Runner.run(self.openai_agent, prompt)
            print('Waiting another 10 seconds before shutdown...')
            await asyncio.sleep(10)
        await asyncio.sleep(0.2)
        return result

    def tools(self):
        return asyncio.run(self.mcp_server_stack.list_available_mcp_tools())