import base64
import io
import os
import unittest

import PIL.Image

from test.unit.test_agent import mocked_agent


class TestDockerAPI(unittest.TestCase):
    def setUp(self):
        self.a = mocked_agent()

    def test_initial_response(self):
        response = self.a.docker_exec('echo $DISPLAY')
        self.assertEqual({'stdout': 'host.docker.internal:0.0\n', 'stderr': '', 'return_code': 0}, response)

    def test_clicking_somewhere(self):
        response = self.a.docker_exec('DISPLAY=host.docker.internal:0.0 xdotool mousemove 300 120 click 1')
        print(response)
        self.assertEqual(response['return_code'], 0)

    def test_getting_screenshot(self):
        response = self.a.get_screenshot()
        image_data_b64 = response['image_data']
        self.assertIsInstance(image_data_b64, str)
        decoded = base64.b64decode(image_data_b64)
        self.assertIsInstance(decoded, bytes)
        img = PIL.Image.open(io.BytesIO(decoded))
        os.makedirs('logs', exist_ok=True)
        img.save('logs/test_screenshot.png')

