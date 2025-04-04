import unittest

from agent.paperclip_agent import Agent


class TestToolsAvailable(unittest.TestCase):
    def test_puppeteer_tools_available(self):
        a = Agent()
        tools = a.tools()
        assert any(tool.name.startswith('puppeteer') for tool in tools), "No puppeteer tools available"