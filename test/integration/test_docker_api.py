import unittest

from test.resources import example_response
from test.unit.test_agent import mocked_agent


class TestDockerAPI(unittest.TestCase):
    def setUp(self):
        self.a = mocked_agent()

    def test_initial_response(self):
        print(self.a.docker_exec('echo $DISPLAY'))
