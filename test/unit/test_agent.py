import unittest
from unittest.mock import Mock

from agent.paperclip_agent import Agent
from test.resources import example_response


def mocked_agent():
    a = Agent(client='no_client')
    example_request_mock = Mock()
    example_request_mock.return_value.output = example_response
    a.openai_api_request = example_request_mock
    return a


class TestAgent(unittest.TestCase):
    def setUp(self):
        self.a = mocked_agent()

    def test_initial_response(self):
        r = self.a.get_initial_response()
        self.assertEqual(r.output, example_response)
