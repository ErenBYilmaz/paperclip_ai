import asyncio
import json
import os
from typing import Optional

import agents
from agents import Runner
from browser_automation_client import VM


def load_openai_environment_variables():
    for k in ['OPENAI_API_KEY', 'OPENAI_ORG_ID', 'OPENAI_PROJECT_ID']:
        if k not in os.environ:
            with open('/run/secrets/openai_config', 'r') as f:
                data = json.load(f)
                os.environ[k] = data[k]


class Agent:
    def __init__(self, vm: Optional[VM] = None, mcp_servers=None):
        if vm is None:
            vm = VM.create()
        load_openai_environment_variables()
        if mcp_servers is None:
            mcp_servers = []
        self.mcp_servers = mcp_servers
        mcp_config_path = os.path.join(os.path.dirname(__file__), 'mcp.json')
        with open(mcp_config_path, 'r') as f:
            mcp_config = json.load(f)
        self.openai_agent = agents.Agent(
            name='Assistant',
            instructions="You are a helpful assistant. You will be given a series of tasks to perform. ",
            mcp_config=mcp_config,
        )
        self.vm = vm

    def run(self, prompt: str):
        return asyncio.run(Runner.run(self.openai_agent, prompt))
