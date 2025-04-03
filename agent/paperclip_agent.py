import time

from openai import OpenAI

from docker_api import VM, docker_exec


class Agent:
    def __init__(self, vm=None, client=None):
        if vm is None:
            vm = VM.create()
        if client is None:
            OpenAI()
        self.client = client
        self.vm = vm

    def get_initial_response(self):
        response = self.openai_api_request()
        print(response.output)
        return response

    def docker_exec(self, command):
        return docker_exec(f'DISPLAY={self.vm.display} ' + command, self.vm.container_name)

    # def get_screenshot(vm):
    #     """
    #     Takes a screenshot, returning raw bytes.
    #     """
    #     cmd = (
    #         f"export DISPLAY={vm.display} && "
    #         "import -window root png:-"
    #     )
    #     screenshot_bytes = docker_exec(cmd, vm.container_name, decode=False)
    #     return screenshot_bytes

    def openai_api_request(self):
        return self.client.responses.create(
            model="computer-use-preview",
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
                # Optional: include a screenshot of the initial state of the environment
                # {
                #     type: "input_image",
                #     image_url: f"data:image/png;base64,{screenshot_base64}"
                # }
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
