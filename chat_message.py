import uuid
from typing import Optional, Sequence, Mapping, Any

import ollama


class ChatMessage(ollama.Message):
    call_id: str = None
    """Call ID as used by OpenAI API to relate tool calls to function outputs.
    Only filled if the message is a response to a tool call including the tools outputs."""

    class ToolCall(ollama.Message.ToolCall):
        call_id: str
        """Call ID as used by OpenAI API to relate tool calls to function outputs."""

    tool_calls: Optional[Sequence[ToolCall]] = None
    """
    Tools calls to be made by the model.
    """


def create_tool_call_object(name: str, arguments: Mapping[str, Any]):
    return ChatMessage.ToolCall(
        function=ollama.Message.ToolCall.Function(
            name=name,
            arguments=arguments,
        ),
        call_id=str(uuid.uuid4())
    )
