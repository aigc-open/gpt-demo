from gpt_demo import ChatBotDemo
from fire import Fire
import json


class ChatBotDemo_(ChatBotDemo):
    TITLE = "GPT-4o 问答"

    @classmethod
    async def generate(cls, *args, **kwargs):
        # todo:
        for i in range(100):
            yield str(int(time.time()))


if __name__ == "__main__":
    Fire(ChatBotDemo_.run)
