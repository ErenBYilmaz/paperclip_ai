import unittest

from docker_api import VM


class TestDockerAPI(unittest.TestCase):
    def test_creating_vm(self):
        vm = VM.create()
        assert isinstance(vm, VM)