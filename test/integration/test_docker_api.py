import unittest

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
