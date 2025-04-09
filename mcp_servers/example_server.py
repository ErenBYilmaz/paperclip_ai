import os.path

from agent.mcp_servers import MCPServerStack
from mcp_servers.wrapper import MCPServerWrapper

mcp = MCPServerWrapper(name="Demo", wrapped_servers=MCPServerStack.from_config(os.path.join(os.path.dirname(__file__), 'wrapped_mcps.json'))).get_server()


@mcp.tool()
def secret_computation(a: int, b: int) -> str:
    """Does some secret computation based on two numbers. It will return a single number that is the result of that computation"""
    return f'The result of the secret computation is {a + b + 42}'

@mcp.tool()
def get_current_weather() -> str:
    return f'The weather is sunny, with volcanic ashes in the sky.'


# @mcp.resource("retrieve_user_id://{name}")
# def retrieve_user_id(name: str) -> str:
#     """Gets the user id from the name of the user"""
#     return f"Hello, {name}!"

if __name__ == '__main__':
    mcp.settings.port = 16041
    mcp.run(transport='stdio')