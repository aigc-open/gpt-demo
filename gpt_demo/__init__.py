import torch
import time
from PIL import Image
import gradio as gr
import os
from threading import Thread
from gpt_demo.cut_messages import string_token_count
from loguru import logger
import json


class ChatBotDemo:

    CSS = """
    .duplicate-button {
    margin: auto !important;
    color: white !important;
    background: black !important;
    border-radius: 100vh !important;
    }
    """

    TITLE = "演示"

    @classmethod
    async def generate(cls, *args, **kwargs):
        for i in range(100):
            yield str(int(time.time()))

    @classmethod
    async def stream_chat(cls, message: str, history: list, temperature: float, max_length: int):
        conversation = []
        for prompt, answer in history:
            conversation.extend([{"role": "user", "content": prompt}, {
                                "role": "assistant", "content": answer}])
        conversation.append({"role": "user", "content": message})

        logger.info(f"问题： -\n{conversation}")
        buffer = ""
        start_time = time.time()
        async for data in cls.generate(message=conversation, temperature=temperature, max_length=max_length):
            buffer += data
            yield buffer
        logger.info(
            f"tps(吞吐): {string_token_count(buffer)/(time.time()- start_time)}")

    @classmethod
    async def page(cls,
                   examples=[]):
        with gr.Blocks(css=cls.CSS, theme="soft", fill_height=True) as demo:
            gr.HTML(f"<h1><center>{cls.TITLE}</center></h1><br>")
            gr.ChatInterface(
                fn=cls.stream_chat,
                chatbot=gr.Chatbot(height=600),
                fill_height=True,
                additional_inputs_accordion=gr.Accordion(
                    label="⚙️ Parameters", open=False, render=False),
                additional_inputs=[
                    gr.Slider(
                        minimum=0.1,
                        maximum=1.0,
                        step=0.1,
                        value=0.0,
                        label="Temperature",
                        render=False,
                    ),
                    gr.Slider(
                        minimum=128,
                        maximum=8192,
                        step=1,
                        value=1024,
                        label="Max Length",
                        render=False,
                    )
                ],
                examples=examples,
                cache_examples=False,
            )
        return demo

    @classmethod
    async def run(cls, port: int = 7860, examples_file: str = ""):
        if examples_file:
            with open(examples_file, "r") as f:
                examples = json.loads(f.read())
        else:
            examples = []
        demo = await cls.page(examples=examples)
        demo.launch(server_name="0.0.0.0", server_port=port)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=Config.port)
