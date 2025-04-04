import unittest


class TestShellCommand(unittest.TestCase):
    def test_shell_command(self):
        # Test shell command execution
        from browser_api.shell_command import ShellCommand

        # Example command to test
        result = ShellCommand(command="echo", args=["Hello, World!"]).execute()

        # Check if the command executed successfully
        self.assertEqual(result.returncode, 0)
        self.assertIn("Hello, World!", result.stdout)
