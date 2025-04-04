import base64
import io
import os
import unittest

import PIL.Image
import numpy

from agent.paperclip_agent import Agent


class TestDockerAPI(unittest.TestCase):
    def setUp(self):
        self.a: Agent = Agent()

    def test_initial_response(self):
        response = self.a.docker_exec('echo $DISPLAY')
        self.assertEqual({'stdout': 'host.docker.internal:0.0\n', 'stderr': '', 'return_code': 0}, response)

    def test_clicking_into_the_address_bar(self):
        response = self.a.docker_exec('DISPLAY=host.docker.internal:0.0 xdotool mousemove 300 120 click 1')
        print(response)
        self.assertEqual(response['return_code'], 0)

    def test_screenshot(self):
        image_data_b64 = self.a.img_to_base64(self.a.cropped_screenshot())
        decoded = base64.b64decode(image_data_b64)
        self.assertIsInstance(decoded, bytes)
        img = PIL.Image.open(io.BytesIO(decoded))
        array = numpy.array(img)
        os.makedirs('logs', exist_ok=True)
        img.save('logs/test_screenshot.png')
        black_ratio = numpy.count_nonzero(array == 0) / array.size
        assert black_ratio < 0.2
