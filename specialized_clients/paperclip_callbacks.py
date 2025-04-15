import typing_extensions

from callback import ChatCallback
from frontend_v3 import Chat

if typing_extensions.TYPE_CHECKING:
    from specialized_clients.paperclip_agent import PaperclipAgent


class SaveOnContinuation(ChatCallback):
    def __init__(self, agent: 'PaperclipAgent', save_path: str):
        self.save_path = save_path
        self.agent = agent

    async def on_continuation(self, chat: Chat):
        await self.agent.save_game(await self.agent.get_game_state_json(), self.save_path)
