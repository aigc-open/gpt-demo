import torch
import time
from PIL import Image
import gradio as gr
import os
from threading import Thread
from gpt_cut_messages import cut_messages, cut_string, messages_token_count, string_token_count
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
import json
import dotenv
import asyncio
dotenv.load_dotenv()


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
    system_messages = [ {"role": "system", "content": f"你是一个有用的助手"}]

    @classmethod
    def generate(cls, *args, **kwargs):
        for i in range(100):
            yield str(int(time.time()))

    @classmethod
    def examples(cls):
        return []

    @classmethod
    def stream_chat(cls, message: str, history: list, temperature: float, max_length: int):
        conversation = []
        conversation += cls.system_messages
        for prompt, answer in history:
            conversation.extend([{"role": "user", "content": prompt}, {
                                "role": "assistant", "content": answer}])
        conversation.append({"role": "user", "content": message})

        logger.info(f"问题： {conversation}")
        buffer = ""
        start_time = time.time()
        for data in cls.generate(message=conversation, temperature=temperature, max_length=max_length):
            buffer += data
            yield buffer
        tps = string_token_count(buffer)/(time.time()- start_time)
        logger.info(
            f"tps(吞吐): {tps}")
        gr.Info(f"Token Per Seconds(吞吐): {round(tps, 2)} ℹ️", duration=5)

    @classmethod
    def page(cls, examples=[]):
        if not examples:
            examples = cls.examples()
        gr.ChatInterface(
            fn=cls.stream_chat,
            chatbot=gr.Chatbot(height=600),
            fill_height=True,
            title=cls.TITLE,
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
            submit_btn="🟢 发送",
            stop_btn="🛑 停止",
            retry_btn="🔄  重试",
            undo_btn="↩️ Undo",
            clear_btn="🗑️  清除",
        )

    @classmethod
    def read_examples(cls, examples_file:str):
        with open(examples_file, "r") as f:
            examples = json.loads(f.read())
        return examples

    @classmethod
    def run(cls, port: int = 7860, examples_file: str = "", share=False):
        if examples_file:
            examples = cls.read_examples(examples_file=examples_file)
        else:
            examples = []
        with gr.Blocks(css=cls.CSS, theme="soft", fill_height=True) as demo:
            cls.page(examples=examples)
        demo.launch(server_name="0.0.0.0", server_port=port, share=share)


class EnvConfig:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL")
    WEIXIN_ROBOT_KEY = os.environ.get("WEIXIN_ROBOT_KEY")
    WEIXIN_ROBOT_KEY_SOGOU = os.environ.get("WEIXIN_ROBOT_KEY_SOGOU")
    DEEPSEEK_CODEBASE_MODEL = os.environ.get("DEEPSEEK_CODEBASE_MODEL")
    DEEPSEEK_CODECHAT_MODEL = os.environ.get("DEEPSEEK_CODECHAT_MODEL")
    DEEPSEEK_CODECHAT_URL= os.environ.get("DEEPSEEK_CODECHAT_URL")
    DEEPSEEK_CODEBASE_URL= os.environ.get("DEEPSEEK_CODEBASE_URL")
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
