import unittest

from agent.paperclip_agent import Agent


class TestOpenAIRequest(unittest.TestCase):
    def test_openai_request(self):
        a = Agent()