from gpt_demo import ChatBotDemo, EnvConfig
from fire import Fire
import json
import gradio as gr
from openai import OpenAI
from gpt_demo.examples import Examples
from loguru import logger
import time
from gpt_cut_messages import cut_messages, cut_string, messages_token_count, string_token_count
from llm_knowledge_function import LocalKnowledge

knowledger = LocalKnowledge(uri="./.demo-milvus.db",
                            model_name="moka-ai/m3e-base",
                            cache_folder="/root/.cache/huggingface/hub/")


class ChatBotDemo_(ChatBotDemo):
    TITLE = "知识库上传问答"
    client = OpenAI(api_key=EnvConfig.OPENAI_API_KEY,
                    base_url=EnvConfig.OPENAI_BASE_URL)
    model = EnvConfig.OPENAI_MODEL

    @classmethod
    def examples(cls):
        return Examples.simple_chat()

    @classmethod
    def stream_chat(cls, message: str, history: list, temperature: float, max_length: int, knowledge_file):
        conversation = []

        for prompt, answer in history:
            conversation.extend([{"role": "user", "content": prompt}, {
                                "role": "assistant", "content": answer}])
        conversation.append({"role": "user", "content": message})
        cut_messages(conversation, token_limit=2048)
        if knowledge_file:
            docs = knowledger.similarity_search(
                query=message, k=4, expr=f'namespace == "{knowledge_file}"')
            knowledge_list = []
            for doc in docs:
                knowledge_list.append(doc.page_content)
                knowledge_str = '\n'.join(knowledge_list)
                knowledge_str = cut_string(str=knowledge_str, token_limit=2048)
                conversation.append(
                    {"role": "system", "content": f"```{knowledge_str}```"})

        logger.info(f"问题： {conversation}")
        buffer = ""
        start_time = time.time()
        for data in cls.generate(message=conversation, temperature=temperature, max_length=max_length):
            buffer += data
            yield buffer
        tps = string_token_count(buffer)/(time.time() - start_time)
        logger.info(
            f"tps(吞吐): {tps}")
        gr.Info(f"Token Per Seconds(吞吐): {round(tps, 2)} ℹ️", duration=5)

    @classmethod
    def page(cls, examples=[]):
        def update_knowledge():
            def to_milvus(filepath: str, chunk_size: int):
                knowledger.filename_to_milvus(
                    filename=filepath, chunk_size=chunk_size, namespace=filepath)
                return filepath
            with gr.Accordion(label="⚙️ 知识库", open=False, render=True):
                with gr.Row():
                    knowledge_file = gr.File(
                        label="上传知识库", file_count="single")
                    with gr.Column():
                        chunk_size = gr.Number(label="chunk_size", value=1000)
                        btn = gr.Button(value="同步知识库")
            btn.click(to_milvus, inputs=[
                      knowledge_file, chunk_size], outputs=[knowledge_file])
            return knowledge_file

        if not examples:
            examples = cls.examples()
        gr.ChatInterface(
            fn=cls.stream_chat,
            chatbot=gr.Chatbot(height=600),
            fill_height=True,
            title=cls.TITLE,
            additional_inputs_accordion=gr.Accordion(
                label="⚙️ 配置参数", open=False, render=False),
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
                ),
                update_knowledge()
            ],
            examples=[],
            cache_examples=False,
            submit_btn="🟢 发送",
            stop_btn="🛑 停止",
            retry_btn="🔄  重试",
            undo_btn="↩️ Undo",
            clear_btn="🗑️  清除",
        )

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
