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
from gpt_demo.spider import SimpleSpiderParams, SimpleSpider, PagerSpider, AIBotCNSpider, SogouSpider, NewsResponse, HuggingfaceSpider
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage


def init_table():
    db = TinyDB(storage=MemoryStorage)
    ai_table = db.table('ai')
    for name in ["ai_info", "sogou", "hf", "paper"]:
        ai_table.insert({'markdown': "", "name": name})
    return ai_table


class Main:
    ai_table = init_table()

    @classmethod
    def ai_info(cls):
        spider = AIBotCNSpider()
        resp: NewsResponse = spider.run(to_weixin_robot=True)
        if resp.info_weixin:
            res = '<font color="warning"> 昨日AI资讯 </font>\n' + resp.info_weixin
            cls.send_WWXRobot(text=res)
        cls.update_info(markdown=resp.info_markdown, name="ai_info")
        return resp.info_markdown

    @classmethod
    def sogou(cls):
        spider = SogouSpider()
        resp: NewsResponse = spider.run(to_weixin_robot=True)
        if resp.info_weixin:
            res = '<font color="warning"> AI行业趋势洞察 </font>\n' + resp.info_weixin
            cls.send_WWXRobot(text=res, key=EnvConfig.WEIXIN_ROBOT_KEY_SOGOU)
        cls.update_info(markdown=resp.info_markdown, name="sogou")
        return resp.info_markdown

    @classmethod
    def hf(cls):
        spider = HuggingfaceSpider()
        resp: NewsResponse = spider.run(to_weixin_robot=True)
        if resp.info_weixin:
            res = '<font color="warning"> 昨日开源大模型 </font>\n' + resp.info_weixin
            cls.send_WWXRobot(text=res, key=EnvConfig.WEIXIN_ROBOT_KEY_SOGOU)
        cls.update_info(markdown=resp.info_markdown, name="hf")
        return resp.info_markdown

    @classmethod
    def paper(cls):
        spider = PagerSpider()
        resp: NewsResponse = spider.run(to_weixin_robot=True)
        if resp.info_weixin:
            res = '<font color="warning"> 昨日AI论文 </font>\n' + resp.info_weixin
            cls.send_WWXRobot(text=res, key=EnvConfig.WEIXIN_ROBOT_KEY_SOGOU)
        cls.update_info(markdown=resp.info_markdown, name="paper")
        return resp.info_markdown

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
            if type_ == "最新实时新闻":
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
