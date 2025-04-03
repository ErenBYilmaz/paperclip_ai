import unittest
from unittest.mock import Mock, PropertyMock

from agent.paperclip_agent import Agent
from test.resources import example_response

patch_returns_example_response = unittest.mock.patch('agent.paperclip_agent.Agent.openai_api_request', )
example_request_mock = Mock()
example_request_mock.return_value.output = example_response

class TestAgent(unittest.TestCase):
    def setUp(self):
        self.a = Agent(client='no_client')
        self.a.openai_api_request = example_request_mock

    def test_initial_response(self):
        r = self.a.get_initial_response()
        self.assertEqual(r.output, example_response)