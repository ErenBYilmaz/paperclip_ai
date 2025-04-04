import unittest
from unittest.mock import Mock

import numpy

from agent.paperclip_agent import Agent
from test.resources import example_response, example_screenshot_response


def mocked_agent():
    a = Agent(client='no_client')
    example_request_mock = Mock()
    example_request_mock.return_value.output = example_response
    example_screenshot_mock = Mock()
    example_screenshot_mock.return_value = example_screenshot_response
    a.openai_api_request = example_request_mock
    a.get_screenshot = example_screenshot_mock
    return a


class TestAgent(unittest.TestCase):
    def setUp(self):
        self.a = mocked_agent()

    def test_initial_response(self):
        r = self.a.get_initial_response()
        self.assertEqual(r.output, example_response)

    def test_encode_decode_screenshot(self):
        image_data_b64 = self.a.get_screenshot()['image_data']
        decoded = self.a.base64_to_img(image_data_b64)
        encoded = self.a.img_to_base64(decoded)
        decoded_2 = self.a.base64_to_img(encoded)
        assert numpy.array_equal(decoded, decoded_2)