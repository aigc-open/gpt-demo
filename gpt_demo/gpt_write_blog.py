from gpt_demo import ChatBotDemo, EnvConfig
from fire import Fire
import json
from openai import OpenAI
from gpt_demo.examples import Examples
import gradio as gr

copy_code = """
function copyToClipboard() {
    var textToCopy = document.getElementById("text-output").innerText;
    navigator.clipboard.writeText(textToCopy).then(function() {
        alert("复制成功");
    }, function(err) {
        alert("复制失败: ", err);
    });
}
"""

class ChatBotDemo_(ChatBotDemo):
    TITLE = "博客撰写"
    client = OpenAI(api_key=EnvConfig.OPENAI_API_KEY,
                    base_url=EnvConfig.OPENAI_BASE_URL)
    model = EnvConfig.OPENAI_MODEL
    system_messages = [{"role": "system", "content": f"你是一个技术丰富的技术博客专家"},
                       {"role": "system", "content": """
    # 根据要求写一篇博客
    - 格式以markdown格式返回，返回格式必须严格按markdown返回
    """}]

    @classmethod
    def examples(cls):
        return [["请你写一个关于wget 的文章，最好包含使用说明和基本概念"]]

    @classmethod
    def page(cls, examples=[]):
        gr.HTML("<h1><center>博客撰写小助手</center></h1>")
        with gr.Row():
            text = gr.Textbox(
                label="关键信息",
                info="请你详细描述需要写的博客需求",
                lines=8,
                value="请你写一个关于wget 的文章，最好包含使用说明和基本概念",
            )
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
                    minimum=128,
                    maximum=8192,
                    step=1,
                    value=1024,
                    label="Max Length",
                    render=True,
                )
                gen_btn = gr.Button(value="生成博客")
                copy_btn = gr.Button(value="复制markdown")
        result = gr.Markdown("# 点解生成即可",  elem_id="text-output")
        gen_btn.click(cls.generate, inputs=[
                      text, temperature, max_length], outputs=[result])
        copy_btn.click(fn=None, inputs=[],outputs=[], js=copy_code)

    @classmethod
    def generate(cls, text, temperature, max_length):
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
                data +=  chunk.choices[0].delta.content
                yield data


if __name__ == "__main__":
    Fire(ChatBotDemo_.run)
