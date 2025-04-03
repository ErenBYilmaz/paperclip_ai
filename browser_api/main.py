from typing import Union

from fastapi import FastAPI

app = FastAPI()

with open('/run/secrets/browser_automation_api_key', 'r') as file:
    API_KEY = file.read().strip()

SHELL_WHITELIST = [
    'echo',
]

@app.get("/check_key/{api_key}")
def validate_api_key(api_key: str):
    if api_key != API_KEY:
        return {"key_status": "invalid"}
    return {"key_status": "valid"}


@app.post("/execute_command/{api_key}")
def shell_command(api_key: str, command: str):
    """
    Execute a shell command and return the output.
    """
    import subprocess
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return {"output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr}