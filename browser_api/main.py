import base64

from fastapi import FastAPI

from browser_api.shell_command import ShellCommand

app = FastAPI()

with open('/run/secrets/browser_automation_api_key', 'r') as file:
    API_KEY = file.read().strip()


@app.get("/check_key/{api_key}")
def validate_api_key(api_key: str):
    if api_key != API_KEY:
        return {"key_status": "invalid"}
    return {"key_status": "valid"}


@app.post("/execute_command/{api_key}")
def shell_command(api_key: str, cmd: ShellCommand):
    """
    Execute a shell command and return the output.
    """
    if api_key != API_KEY:
        return {"error": "Invalid API key"}
    result = cmd.execute()
    return {
        'stdout': result.stdout,
        'stderr': result.stderr,
        'return_code': result.returncode,
    }

@app.post("/screenshot/{api_key}")
def screenshot(api_key: str):
    """
    Take a screenshot and return the image data.
    """
    if api_key != API_KEY:
        return {"error": "Invalid API key"}
    result = ShellCommand(command="import -window root -silent png:-").execute(decode=False)
    if result.returncode != 0:
        return {"error": "Failed to take screenshot", "stderr": result.stderr}
    return {
        'image_data': base64.b64encode(result.stdout)
    }

