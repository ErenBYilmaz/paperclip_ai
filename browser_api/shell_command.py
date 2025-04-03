import subprocess
from subprocess import CompletedProcess
from typing import List

from pydantic import BaseModel

class ShellCommand(BaseModel):
    """
    Objects of this class define a command to be run in the shell.
    """
    command: str
    args: List[str]

    def execute(self) -> CompletedProcess[str]:
        return subprocess.run(" ".join([self.command] + self.args), shell=True, capture_output=True, text=True)
