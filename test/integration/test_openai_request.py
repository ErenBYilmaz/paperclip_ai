import unittest

from agent.paperclip_agent import Agent


class TestOpenAIRequest(unittest.TestCase):
    def setUp(self):
        self.a = Agent()

    def test_openai_request(self):
        a = Agent()
        r = a.get_initial_response()
        print(r)

    def test_list_models(self):
        a = Agent()
        models = a.client.models.list()
        assert any(model.id.startswith(a.model) for model in models)
        print([model.id for model in models])

    def test_saying_hello(self):
        r = self.a.run('Hello')
        assert isinstance(r.final_output, str)
        print(r.final_output)

    def test_getting_weather_in_tokyo(self):
        r = self.a.run('Use the browser to get the current weather in Tokyo.')
        assert isinstance(r.final_output, str)
        print(r.final_output)