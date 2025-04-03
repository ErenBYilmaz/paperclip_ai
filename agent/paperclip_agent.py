from openai import OpenAI

from docker_api import VM


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

    def handle_model_action(self, vm, action):
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
                    docker_exec(f"DISPLAY={vm.display} xdotool mousemove {x} {y} click {b}", vm.container_name)

                case "scroll":
                    x, y = int(action.x), int(action.y)
                    scroll_x, scroll_y = int(action.scroll_x), int(action.scroll_y)
                    print(f"Action: scroll at ({x}, {y}) with offsets (scroll_x={scroll_x}, scroll_y={scroll_y})")
                    docker_exec(f"DISPLAY={vm.display} xdotool mousemove {x} {y}", vm.container_name)

                    # For vertical scrolling, use button 4 (scroll up) or button 5 (scroll down)
                    if scroll_y != 0:
                        button = 4 if scroll_y < 0 else 5
                        clicks = abs(scroll_y)
                        for _ in range(clicks):
                            docker_exec(f"DISPLAY={vm.display} xdotool click {button}", vm.container_name)

                case "keypress":
                    keys = action.keys
                    for k in keys:
                        print(f"Action: keypress '{k}'")
                        # A simple mapping for common keys; expand as needed.
                        if k.lower() == "enter":
                            docker_exec(f"DISPLAY={vm.display} xdotool key 'Return'", vm.container_name)
                        elif k.lower() == "space":
                            docker_exec(f"DISPLAY={vm.display} xdotool key 'space'", vm.container_name)
                        else:
                            docker_exec(f"DISPLAY={vm.display} xdotool key '{k}'", vm.container_name)

                case "type":
                    text = action.text
                    print(f"Action: type text: {text}")
                    docker_exec(f"DISPLAY={vm.display} xdotool type '{text}'", vm.container_name)

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