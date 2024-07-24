from gpt_demo import ChatBotDemo
from fire import Fire
import json


class ChatBotDemo_(ChatBotDemo):
    TITLE = "GPT-4o 问答"
    

    @classmethod
    async def generate(cls, *args, **kwargs):
        for i in range(100):
            yield str(int(time.time()))


async def run(port: int = 7860, examples_file: str = ""):
    if examples_file:
        with open(examples_file, "r") as f:
            examples = json.loads(f.read())
    else:
        examples = []
    demo = await ChatBotDemo.page(examples=examples)
    demo.launch(server_name="0.0.0.0", server_port=port)


if __name__ == "__main__":
    Fire(run)
