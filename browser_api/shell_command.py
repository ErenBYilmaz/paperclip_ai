import subprocess
from subprocess import CompletedProcess

from pydantic import BaseModel


class ShellCommand(BaseModel):
    """
    Objects of this class define a command to be run in the shell.
    """
    command: str

    def execute(self, decode=True) -> CompletedProcess[str]:
        return subprocess.run(self.command, shell=True, capture_output=True, text=decode)
