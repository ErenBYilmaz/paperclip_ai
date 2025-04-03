import os
import subprocess


def docker_exec(cmd: str, container_name: str, decode=True) -> str:
    safe_cmd = cmd.replace('"', '\"')
    docker_cmd = f'docker exec {container_name} sh -c "{safe_cmd}"'
    output = subprocess.check_output(docker_cmd, shell=True)
    if decode:
        return output.decode("utf-8", errors="ignore")
    return output


class VM:
    def __init__(self, display, container_name):
        self.display = display
        self.container_name = container_name

    @staticmethod
    def create():
        return VM(display=os.environ['DISPLAY'], container_name="paperclip_vm")
