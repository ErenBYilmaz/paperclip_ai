import typing

import ollama

if typing.TYPE_CHECKING:
    from frontend_v3 import Chat


class ChatCallback:
    async def after_tool_call(self, chat: 'Chat', tool: ollama.Message.ToolCall, tool_response):
        raise NotImplementedError('Abstract method')


class AfterToolCallAnotherTool(ChatCallback):
    def __init__(self, first_tool_name: str, other_tool_call: ollama.Message.ToolCall):
        self.first_tool_name = first_tool_name
        self.other_tool_call = other_tool_call

    async def after_tool_call(self, chat: 'Chat', tool: ollama.Message.ToolCall, tool_response):
        if tool.function.name == self.first_tool_name:
            await chat.call_tool_and_add_output_message(self.other_tool_call)


class RemoveInvisibleHTML(ChatCallback):
    async def after_tool_call(self, chat: 'Chat', tool: ollama.Message.ToolCall, tool_response):
        if tool.function.name == 'playwright_get_visible_html':
            last_message = chat.messages[-1]
            content = last_message.content
            html_content = '\n'.join(content.splitlines()[2:])
            # remove any comments
            from lxml import etree

            # print(html_content)
            parser = etree.HTMLParser()
            tree = etree.fromstring(html_content, parser)

            remove_xpaths = [
                '//comment()',
                '//script',
                '//*[contains(@style, "display:none")]',
                '//*[contains(@style, "display: none")]',
            ]

            for path in remove_xpaths:
                for element in tree.xpath(path):
                    p = element.getparent()
                    p.remove(element)
            html_content = etree.tostring(tree, encoding='unicode', method='html')
            last_message.content = html_content
