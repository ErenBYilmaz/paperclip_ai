import unittest

from agent.paperclip_agent import Agent


class TestOpenAIRequest(unittest.TestCase):
    def test_openai_request(self):
        a = Agent()
        r = a.get_initial_response()
        print(r)

    def test_list_models(self):
        a = Agent()
        models = a.client.models.list()
        assert any(model.id.startswith(a.model) for model in models)
        print([model.id for model in models])