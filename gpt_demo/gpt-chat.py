from gpt_demo import ChatBotDemo,EnvConfig
from fire import Fire
import json
from openai import OpenAI


class ChatBotDemo_(ChatBotDemo):
    TITLE = "GPT 问答"
    client = OpenAI(api_key=EnvConfig.OPENAI_API_KEY, base_url=EnvConfig.OPENAI_BASE_URL)
    model = EnvConfig.OPENAI_MODEL

    @classmethod
    def generate(cls, *args, **kwargs):
        completion = cls.client.chat.completions.create(
            model=cls.model,
            max_tokens=kwargs["max_length"],
            messages=kwargs["message"],
            temperature=kwargs["temperature"],
            stream=True
        )
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

if __name__ == "__main__":
    Fire(ChatBotDemo_.run)
