from fire import Fire
import time
import datetime
import requests
from gpt_demo import EnvConfig
from WorkWeixinRobot.work_weixin_robot import WWXRobot
from bs4 import BeautifulSoup
from openai import OpenAI
from gpt_demo import EnvConfig
from pydantic import BaseModel
from typing import List
from loguru import logger
import schedule
import gradio as gr
import threading
from gpt_demo.spider import SimpleSpiderParams, SimpleSpider, PagerSpider, AIBotCNSpider, SogouSpider, HuggingfaceSpider
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage


def init_table():
    # db = TinyDB(storage=MemoryStorage)
    db = TinyDB('db.json')
    ai_table = db.table('ai')
    for name in ["ai_info", "sogou", "hf", "paper"]:
        if not ai_table.search(Query().name == name):
            ai_table.insert({'markdown': "", "name": name})
    return ai_table


def format_weixin(sumary, time_, url, title="查看详情"):
    return f"""
> 内容概要: <font color="comment"> {sumary} </font>
> 发表时间: <font color="comment"> {time_} </font>
> 链接地址: <font color="comment"> [{title}]({url}) </font>
"""


class Main:
    ai_table = init_table()

    @classmethod
    def has_table_value(cls, name) -> bool:
        return len(cls.ai_table.search(Query().name == name)) > 0

    @classmethod
    def set_table_value(cls, name):
        return cls.ai_table.insert({'name': name, 'url': name})

    @classmethod
    def json_to_weixin(cls, info_json):
        data = ""
        str_length = 0
        for info in info_json:
            if not cls.has_table_value(info.get("链接地址")):
                msg =  format_weixin(sumary=info.get(
                    "内容概要"), time_=info.get("发表时间"), url=info.get("链接地址"), title=info.get("标题"))
                if len(data) + len(msg) > 4000:
                    break
                cls.set_table_value(info.get("链接地址"))
                data += msg
            else:
                logger.info(f"dumplicate data: {info}")
        logger.info(f"weixin data length: {len(data)}")
        return data

    @classmethod
    def json_to_markdown(cls, info_json):
        data = "| 标题 | 内容概要 | 发表时间 | 链接地址 |\n| --- | --- | --- | --- |\n"
        for info in info_json:
            data += f"""| {info.get("标题")} | {info.get("内容概要")} | {info.get("发表时间")} | [查看详情]({info.get("链接地址")}) |\n"""
        return data

    @classmethod
    def ai_info(cls):
        spider = AIBotCNSpider()
        info_json = spider.run(
            to_weixin_robot=True)
        if info_json:
            res = '<font color="warning"> 昨日AI资讯 </font>\n' + \
                cls.json_to_weixin(
                    info_json) + f'\n<font color="warning"> {spider.generate_warm_words()} </font>'
            cls.send_WWXRobot(text=res)
        cls.update_info(markdown=cls.json_to_markdown(
            info_json), name="ai_info")
        return info_json

    @classmethod
    def sogou(cls):
        spider = SogouSpider()
        info_json = spider.run(
            to_weixin_robot=True)
        if info_json:
            res = '<font color="warning"> AI行业趋势洞察 </font>\n' + \
                cls.json_to_weixin(
                    info_json) + f'\n<font color="warning"> {spider.generate_warm_words()} </font>'
            cls.send_WWXRobot(text=res, key=EnvConfig.WEIXIN_ROBOT_KEY_SOGOU)
        cls.update_info(markdown=cls.json_to_markdown(info_json), name="sogou")
        return info_json

    @classmethod
    def hf(cls):
        spider = HuggingfaceSpider()
        info_json = spider.run(
            to_weixin_robot=True)
        if info_json:
            res = '<font color="warning"> 昨日开源大模型 </font>\n' + \
                cls.json_to_weixin(
                    info_json) + f'\n<font color="warning"> {spider.generate_warm_words()} </font>'
            cls.send_WWXRobot(text=res, key=EnvConfig.WEIXIN_ROBOT_KEY_SOGOU)
        cls.update_info(markdown=cls.json_to_markdown(info_json), name="hf")
        return info_json

    @classmethod
    def paper(cls):
        spider = PagerSpider()
        info_json = spider.run(
            to_weixin_robot=True)
        if info_json:
            res = '<font color="warning"> 昨日AI论文 </font>\n' + \
                cls.json_to_weixin(
                    info_json) + f'\n<font color="warning"> {spider.generate_warm_words()} </font>'
            cls.send_WWXRobot(text=res, key=EnvConfig.WEIXIN_ROBOT_KEY_SOGOU)
        cls.update_info(markdown=cls.json_to_markdown(info_json), name="paper")
        return info_json

    @classmethod
    def send_WWXRobot(cls, text, key=EnvConfig.WEIXIN_ROBOT_KEY):
        wwxrbt = WWXRobot(key=key)
        wwxrbt.send_markdown(content=text)

    @classmethod
    def update_info(cls, markdown, name):
        cls.ai_table.update({'markdown': markdown,
                            "name": name}, Query().name == name)

    @classmethod
    def get_info(cls, name):
        info = cls.ai_table.search(Query().name == name)[0].get("markdown")
        if not info:
            logger.warning("无数据，尝试开始获取")
            info = "### 努力拉取中,请稍等1分钟..."
            cls.update_info(markdown=info, name=name)
            threading.Thread(target=getattr(cls, name)).start()
        return info

    @classmethod
    def all(cls):
        logger.info("开始制作")
        cls.ai_info()
        cls.hf()
        cls.paper()
        logger.info("完成推送")

    @classmethod
    def cron(cls):
        logger.info("等待任务")
        schedule.every().day.at("07:00").do(cls.all)
        schedule.every().day.at("09:00").do(cls.sogou)
        schedule.every().day.at("15:00").do(cls.sogou)
        while True:
            schedule.run_pending()  # 运行所有到期的任务
            time.sleep(1)

    @classmethod
    def run(cls, port: int = 7860):
        def change(type_):
            if type_ == "昨日AI资讯":
                return cls.get_info("ai_info")
            if type_ == "昨日开源大模型":
                return cls.get_info("hf")
            if type_ == "昨日热门论文":
                return cls.get_info("paper")
            if type_ == "AI行业趋势洞察":
                return cls.get_info("sogou")

        threading.Thread(target=cls.cron).start()
        with gr.Blocks(theme="soft", fill_height=True) as demo:
            gr.HTML("<h1><center>AI小灵通</center></h1>")
            gr.HTML("<h6><center>消息每天会自动同步到企业微信机器人中，方便其他同事共享</center></h6>")
            with gr.Row():
                radio = gr.Radio(
                    ["昨日AI资讯", "昨日开源大模型", "昨日热门论文", "AI行业趋势洞察"], label="资讯类型")
                btn = gr.Button("刷新")
            result = gr.Markdown("### 请选择资讯类型")
            radio.change(fn=change, inputs=radio, outputs=[result])
            btn.click(fn=change, inputs=radio, outputs=[result])
        demo.launch(server_name="0.0.0.0", server_port=port)


if __name__ == "__main__":
    Fire(Main)
