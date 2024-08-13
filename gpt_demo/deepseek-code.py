from gpt_demo import ChatBotDemo, EnvConfig
from fire import Fire
import json
from openai import OpenAI
from gpt_demo.examples import Examples
import gradio as gr


class ChatBotDemo_(ChatBotDemo):
    TITLE = "代码生成"
    # chat_client = OpenAI(api_key=EnvConfig.DEEPSEEK_API_KEY,
    #                      base_url=EnvConfig.DEEPSEEK_CODECHAT_URL)
    code_client = OpenAI(api_key=EnvConfig.DEEPSEEK_API_KEY,
                         base_url=EnvConfig.DEEPSEEK_CODEBASE_URL)
    codebase_model = EnvConfig.DEEPSEEK_CODEBASE_MODEL
    # codechat_model = EnvConfig.DEEPSEEK_CODECHAT_MODEL

    @classmethod
    def examples(cls):
        return [[]]

    @classmethod
    def page_code_generation(cls):
        with gr.Accordion("输入代码"):
            pre_code = gr.Textbox(
                label="代码块",
                info="请你给出代码块的前置信息：最后换行或者空格对结果的影响",
                lines=8,
                value="""
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[0]
    left = []
    right = []
"""
            )
            after_code = gr.Textbox(
                label="代码块",
                info="请你给出代码块的后置信息",
                lines=8
            )
        with gr.Row():
            with gr.Column():
                temperature = gr.Slider(
                    minimum=0.1,
                    maximum=1.0,
                    step=0.1,
                    value=0.0,
                    label="Temperature",
                    render=True,
                )
                max_length = gr.Slider(
                    minimum=32,
                    maximum=8192,
                    step=1,
                    value=64,
                    label="Max Length",
                    render=True,
                )
                line_des = gr.Radio(["单行", "多行"], label="输出要求", value="多行")
            gen_btn = gr.Button(value="生成代码")
        result = gr.Code()
        gen_btn.click(fn=cls.codebase_generate, inputs=[
                      pre_code, after_code, temperature, max_length, line_des], outputs=[result])

    @classmethod
    def page(cls, examples=[]):
        gr.HTML("<h1><center>代码生成小助手</center></h1>")
        cls.page_code_generation()

    @classmethod
    def codechat_generate(cls, text, temperature, max_length):
        messages = cls.system_messages + [{"role": "user", "content": text}]
        completion = cls.client.chat.completions.create(
            model=cls.model,
            max_tokens=max_length,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        data = ""
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                data += chunk.choices[0].delta.content
                yield data

    @classmethod
    def codebase_generate(cls, pre_code="", after_code="", temperature=0, max_length=1024, line_des="多行"):
        if line_des == "单行":
            stop = ["\n"]
        else:
            stop = []
        prompt = f"<｜fim▁begin｜>{pre_code}<｜fim▁hole｜>{after_code}<｜fim▁end｜>"
        completion = cls.code_client.completions.create(
            model=cls.codebase_model,
            prompt=prompt,
            temperature=temperature,
            top_p=1,
            max_tokens=max_length,
            stream=True,
            stop=stop
        )
        data = pre_code
        for chunk in completion:
            if chunk.choices[0].text is not None:
                data += chunk.choices[0].text
                yield data
        data += after_code
        yield data


if __name__ == "__main__":
    Fire(ChatBotDemo_.run)
