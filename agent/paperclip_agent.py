import asyncio
import base64
import io
import json
import os
import time
from typing import Optional, Union

import PIL.Image
import agents
import numpy
from agents import Runner
from typing_extensions import Buffer

from browser_automation_client import VM


def load_openai_environment_variables():
    for k in ['OPENAI_API_KEY', 'OPENAI_ORG_ID', 'OPENAI_PROJECT_ID']:
        if k not in os.environ:
            with open('/run/secrets/openai_config', 'r') as f:
                data = json.load(f)
                os.environ[k] = data[k]


class Agent:
    def __init__(self, vm: Optional[VM] = None, mcp_servers=None):
        if vm is None:
            vm = VM.create()
        load_openai_environment_variables()
        if mcp_servers is None:
            mcp_servers = []
        self.mcp_servers = mcp_servers
        self.openai_agent = agents.Agent(
            name='Assistant',
            instructions="You are a helpful assistant. You will be given a series of tasks to perform. ",
            mcp_servers=self.mcp_servers,
        )
        self.vm = vm

    def run(self, prompt: str):
        return asyncio.run(Runner.run(self.openai_agent, prompt))

    def docker_exec(self, command):
        return self.vm.docker_exec(f'DISPLAY={self.vm.display} ' + command)

    def get_screenshot(self):
        """
        Takes a screenshot, returning raw bytes.
        """
        return self.vm.screenshot()

    def cropped_screenshot(self) -> PIL.Image:
        response = self.get_screenshot()
        array = self.base64_to_img(response['image_data'])
        all_black_rows = numpy.all(array == 0, axis=(0, -1))
        all_black_columns = numpy.all(array == 0, axis=(1, -1))
        array = array[~all_black_columns][:, ~all_black_rows]
        return array

    def img_to_base64(self, a: Union[numpy.ndarray | Buffer]):
        buffer = io.BytesIO()
        PIL.Image.fromarray(a).save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue())

    def base64_to_img(self, image_data_b64: str | Buffer) -> numpy.ndarray:
        decoded = base64.b64decode(image_data_b64)
        img = PIL.Image.open(io.BytesIO(decoded))
        array = numpy.array(img)
        return array

    def openai_api_request(self):
        screenshot_base64 = self.get_screenshot()['image_data']
        return self.client.responses.create(
            model=self.model,
            tools=[{
                "type": "computer_use_preview",
                "display_width": 1024,
                "display_height": 768,
                "environment": "browser"  # other possible values: "mac", "windows", "ubuntu"
            }],
            input=[
                {
                    "role": "user",
                    "content": "Check the latest OpenAI news on bing.com."
                }
            ],
            reasoning={
                "generate_summary": "concise",
            },
            truncation="auto"
        )

    def handle_model_action(self, action):
        """
        Given a computer action (e.g., click, double_click, scroll, etc.),
        execute the corresponding operation on the Docker environment.
        """
        action_type = action.type

        try:
            match action_type:

                case "click":
                    x, y = int(action.x), int(action.y)
                    button_map = {"left": 1, "middle": 2, "right": 3}
                    b = button_map.get(action.button, 1)
                    print(f"Action: click at ({x}, {y}) with button '{action.button}'")
                    self.docker_exec(f"xdotool mousemove {x} {y} click {b}")

                case "scroll":
                    x, y = int(action.x), int(action.y)
                    scroll_x, scroll_y = int(action.scroll_x), int(action.scroll_y)
                    print(f"Action: scroll at ({x}, {y}) with offsets (scroll_x={scroll_x}, scroll_y={scroll_y})")
                    self.docker_exec(f"xdotool mousemove {x} {y}")

                    # For vertical scrolling, use button 4 (scroll up) or button 5 (scroll down)
                    if scroll_y != 0:
                        button = 4 if scroll_y < 0 else 5
                        clicks = abs(scroll_y)
                        for _ in range(clicks):
                            self.docker_exec(f"xdotool click {button}")

                case "keypress":
                    keys = action.keys
                    for k in keys:
                        print(f"Action: keypress '{k}'")
                        # A simple mapping for common keys; expand as needed.
                        if k.lower() == "enter":
                            self.docker_exec(f"xdotool key 'Return'")
                        elif k.lower() == "space":
                            self.docker_exec(f"xdotool key 'space'")
                        else:
                            self.docker_exec(f"xdotool key '{k}'")

                case "type":
                    text = action.text
                    print(f"Action: type text: {text}")
                    self.docker_exec(f"xdotool type '{text}'")

                case "wait":
                    print(f"Action: wait")
                    time.sleep(2)

                case "screenshot":
                    # Nothing to do as screenshot is taken at each turn
                    print(f"Action: screenshot")

                # Handle other actions here

                case _:
                    print(f"Unrecognized action: {action}")

        except Exception as e:
            print(f"Error handling action {action}: {e}")
