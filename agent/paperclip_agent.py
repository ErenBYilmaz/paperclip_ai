import asyncio
import json
import os

import agents
from agents import Runner, ItemHelpers, RunItem

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
            instructions="You are an assistant capable of using a web browser through puppeteer. "
                         "You will be given a task or series of tasks to perform. "
                         "You open a web page, obtain the html content of that page, and then take actions to accomplish the task. "
                         "You are not allowed to take screenshots of the web page because you are not capable of processing them (limited context window).",
            mcp_servers=self.mcp_server_stack.mcp_servers
        )

    def run(self, prompt: str):
        print('Running agent with prompt:', prompt)
        return asyncio.run(self.arun(prompt))

    async def arun(self, prompt: str):
        print('Starting mcp servers...')
        async with self.mcp_server_stack:
            print('servers running')
            result = Runner.run_streamed(self.openai_agent, prompt)
            async for event in result.stream_events():
                self.process_event(event)
            print('Waiting another 10 seconds before shutdown...')
            await asyncio.sleep(10)
        await asyncio.sleep(0.2)
        return result

    def tools(self):
        return asyncio.run(self.mcp_server_stack.list_available_mcp_tools())

    def process_event(self, event: agents.stream_events.StreamEvent):
        # We'll ignore the raw responses event deltas
        if event.type == "raw_response_event":
            return
        # When the agent updates, print that
        elif event.type == "agent_updated_stream_event":
            print(f"Agent updated: {event.new_agent.name}")
            return
        # When items are generated, print them
        elif event.type == "run_item_stream_event":
            item: RunItem = event.item
            if item.type == "tool_call_item":
                print(f"-- Tool was called: {item.raw_item.to_json()}")
            elif item.type == "tool_call_output_item":
                print(f"-- Tool output: {item.output}")
            elif item.type == "reasoning_item_created":
                print(f"-- Tool output: {item.raw_item.to_json()}")
            elif item.type == "message_output_item":
                print(f"-- Message output:\n {ItemHelpers.text_message_output(item)}")
            else:
                print('Unknown event type:', item.type)