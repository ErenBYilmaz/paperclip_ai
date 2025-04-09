from typing import Dict, Callable

import ollama


def get_current_weather() -> str:
    """Find out the current weather at your location. Returns the weather information as a descriptive text."""
    return f'The weather is sunny, with volcanic ashes in the sky.'

def main():
    # prompt = input('> ')
    prompt = 'What is the current weather? good for getting my airplane out and having flight?'
    tools = [get_current_weather]
    tools_by_name: Dict[str, Callable] = {
        tool.__name__: tool
        for tool in tools
    }
    client = ollama.Client(
        host='host.docker.internal'
    )
    response = client.chat(
        'llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        tools=tools
    )
    if response.message.tool_calls:
        for tool in response.message.tool_calls:
            if tool.function.name not in tools_by_name:
                raise ValueError(f"Tool {tool.function.name} not found")
            tool_function = tools_by_name[tool.function.name]
            arguments = tool.function.arguments
            print('Calling tool:', tool_function.__name__, 'with arguments:', arguments)
            tool_response = tool_function(**arguments)
            print('Tool response:', tool_response)


if __name__ == '__main__':
    main()
