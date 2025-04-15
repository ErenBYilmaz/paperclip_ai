import os

from specialized_clients.paperclip_agent import OpenAIPaperclipAgent


async def main():
    agent = OpenAIPaperclipAgent()
    save_path = 'test_save.json'
    async with agent:
        await agent.setup()
        if os.path.isfile(save_path):
            await agent.restore_game(save_path)
        await agent.chat.interaction(agent.initial_prompt(), max_steps=10)
        await agent.save_game(await agent.get_game_state_json(), save_path)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())