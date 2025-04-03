import os
from http.client import responses

import requests


def load_api_key_from_docker_secrets():
    if 'BROWSER_AUTOMATION_API_KEY' in os.environ:
        return os.environ['BROWSER_AUTOMATION_API_KEY']
    with open('/run/secrets/browser_automation_api_key', 'r') as file:
        return file.read().strip()



def docker_exec(cmd: str, container_name: str) -> str:
    # safe_cmd = cmd.replace('"', '\"')
    # docker_cmd = f'docker exec {container_name} /bin/sh -c "{safe_cmd}"'
    # output = subprocess.check_output(docker_cmd, shell=True)
    # if decode:
    #     return output.decode("utf-8", errors="ignore")
    # return output
    cmd, args = cmd.split(" ", 1)
    args_list = args.split(" ")
    # Send a post request to the API
    api_key = load_api_key_from_docker_secrets()
    response = requests.post(
        f"http://{container_name}:8000/execute_command/{api_key}",
        json={
            "command": cmd,
            "args": args_list
        }
    )
    return response.json()


class VM:
    def __init__(self, display, container_name):
        self.display = display
        self.container_name = container_name
        self.api_key = load_api_key_from_docker_secrets()

    @staticmethod
    def create():
        return VM(display=os.environ['DISPLAY'], container_name="paperclip_browser_container")

    def docker_exec(self, cmd: str) -> str:
        response = requests.post(
            f"http://{self.container_name}:8000/execute_command/{self.api_key}",
            json={
                "command": cmd
            }
        )
        return response.json()

    def screenshot(self):
        response = requests.post(
            f"http://{self.container_name}:8000/screenshot/{self.api_key}"
        )
        if response.status_code != 200:
            raise Exception(f"Failed to take screenshot: {response.status_code} {responses[response.status_code]}")
        return response.json()