import asyncio
import json
import os
import unittest

from specialized_clients.paperclip_agent import OpenAIPaperclipAgent, OllamaPaperclipAgent
from test.resources import example_savegame_8_clips_json


class TestAgent(unittest.IsolatedAsyncioTestCase):
    async def test_making_a_paperclip(self):
        agent = OpenAIPaperclipAgent()
        prompt = ('Hello. We are playing the browsergame "Universal Paperclips"! '
                  'I have already opened the web browser for you. '
                  'Get the visible html and click the paperclip-making button. '
                  'Then check the new html of the page and report how many paperclips we have available now.')
        async with agent:
            await agent.setup()
            await agent.chat.interaction(prompt)
            chat = agent.chat
            print(chat.history_str())
            last_message = chat.messages[-1]
            self.assertIn('9', last_message.content)
            await asyncio.sleep(1)

    async def test_reading_html(self):
        agent = OllamaPaperclipAgent()
        prompt = ('Hello. We are playing the browsergame "Universal Paperclips"! '
                  'I have already opened the web browser for you. '
                  'Get the visible html and check how many paperclips we have available.')
        async with agent:
            await agent.setup()
            await agent.chat.interaction(prompt)
            chat = agent.chat
            print(chat.history_str())
            last_message = chat.messages[-1]
            self.assertIn('8', last_message.content)
            await asyncio.sleep(1)

    async def test_saving_and_loading_game(self):
        agent = OllamaPaperclipAgent()
        async with agent:
            await agent.setup()
            initial_state = await agent.get_game_state_json()
            initial_data = json.loads(initial_state)
            await agent.save_game(initial_state, 'test.json')
            loaded_state = agent.load_game('test.json')
            loaded_data = json.loads(loaded_state)
            self.assertEqual(initial_data, loaded_data)

    async def test_loading_and_saving_game(self):
        agent = OllamaPaperclipAgent()
        async with agent:
            await agent.setup()
            initial_state = example_savegame_8_clips_json
            with open('test_8.json', 'w') as f:
                f.write(initial_state)
            initial_data = json.loads(initial_state)
            initial_game = json.loads(initial_data['saveGame'])
            await agent.restore_game('test_8.json')
            loaded_state = await agent.get_game_state_json()
            loaded_data = json.loads(loaded_state)
            loaded_game = json.loads(loaded_data['saveGame'])
            for key in ["clips", 'unusedClips', 'clipRate']:
                self.assertEqual(initial_game[key], loaded_game[key])


class TestPlayingTheGame(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = OpenAIPaperclipAgent()

    async def test_playing_the_game(self):
        agent = self.agent
        async with agent:
            await agent.setup()
            if os.path.isfile('test_save.json'):
                await agent.restore_game('savegame.json')
            await agent.chat.interaction(agent.initial_prompt())
            await agent.chat.interaction('Continue making paperclips.')
            await agent.save_game(await agent.get_game_state_json(), 'test_save.json')
