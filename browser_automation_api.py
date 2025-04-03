from typing import Union

from fastapi import FastAPI

app = FastAPI()

with open('/run/secrets/browser_automation_api_key', 'r') as file:
    API_KEY = file.read().strip()

@app.get("/{api_key}")
def read_root(api_key: str):
    if api_key != API_KEY:
        return {"error": "Invalid API key"}
    return {"Hello": "World"}