from gpt_demo import ChatBotDemo
from fire import Fire
import json
import gradio as gr


class _ChatBotDemo_(ChatBotDemo):


    @classmethod
    def run(cls, port: int = 7860, examples_file: str = ""):
        with gr.Blocks(css=cls.CSS, theme="soft", fill_height=True) as demo:
            with gr.Tab("GPT通用回答"):
                from gpt_demo.gpt_chat import ChatBotDemo_
                ChatBotDemo_.page()
            with gr.Tab("GPT4o-mini通用回答"):
                from gpt_demo.gpt4o_mini_chat import ChatBotDemo_
                ChatBotDemo_.page()
        demo.launch(server_name="0.0.0.0", server_port=port)


if __name__ == "__main__":
    Fire(_ChatBotDemo_.run)
