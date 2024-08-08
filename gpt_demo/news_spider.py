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


class SimpleSpiderParams(BaseModel):
    url: str = ""
    prompt: str


class SimpleSpider:
    client = OpenAI(api_key=EnvConfig.OPENAI_API_KEY,
                    base_url=EnvConfig.OPENAI_BASE_URL)
    model = EnvConfig.OPENAI_MODEL

    def __init__(self):
        self.spider_results = []

    def chat_api(self, *args, **kwargs):
        completion = self.client.chat.completions.create(
            model=self.model,
            max_tokens=kwargs["max_length"],
            messages=kwargs["message"],
            temperature=kwargs["temperature"],
            stream=False
        )
        return completion.choices[0].message.content

    def request(self, url):
        html = requests.get(url).text
        return html

    def run(self, params: List[SimpleSpiderParams], max_length=4096, temperature=0.7, system_prompt="你是一个html解析助手"):
        for param in params:
            try:
                html = self.request(url=param.url)
            except Exception as e:
                logger.exception(e)
                continue
            message = [{"role": "system", "content": system_prompt}, {
                "role": "system", "content": f"```{html}```"}, {"role": "user", "content": param.prompt}]
            self.spider_results.append(self.chat_api(
                max_length=max_length, temperature=temperature, message=message))

    def summary(self, prompt, max_length=4096, temperature=0.7, system_prompt="你是一个markdown关键信息提取器"):
        if not self.spider_results:
            raise Exception("没有抓取到数据,网络异常")
        results_str = '\n\n'.join(self.spider_results)
        message = [{"role": "system", "content": system_prompt}, {
            "role": "system", "content": f"```{results_str}```"}, {"role": "user", "content": prompt}]
        return self.chat_api(max_length=max_length, temperature=temperature, message=message)


class PagerSpider(SimpleSpider):
    def request(self, url):
        url = "https://hub-api.baai.ac.cn/api/v3/paper/list"
        html = requests.post(
            url, json={"page": 1, "type": "new", "area": "cs.AI"}).text
        return html


class AIBotCNSpider(SimpleSpider):
    def request(self, url):
        url = "https://ai-bot.cn/daily-ai-news/"
        html = requests.get(url).text

        soup = BeautifulSoup(html, 'html.parser')
        news_items = soup.find_all('div', class_='news-item')
        xml_str = ""
        count = 0
        for elem in news_items:
            xml_str += str(elem)
            count += 1
            if count > 5:
                break
        return xml_str


class Main:
    prompt = """
    - 请你将上面内容，解析成结构化数据
    - 请你直接返回markdown 表格数据格式，要求字段为内容概要，发表时间, 链接地址
    - 如果没有发表时间的数据，则丢弃不要
    - 链接地址如果没有域名，请加上
    - 不要使用代码块``````包起来

    # 格式如下：
    | 标题 | 内容概要 | 发表时间 | 链接地址 |
    | --- | --- | --- | --- |
    | xxxxx | xxxxx | 2024/08/07 09:32 | xxxxxx |
    """
    normal_prompt = """
    - 筛选出最新的Top5的AI相关资讯，主要范围为模型,结果中不要带这句话
    - 给我写一个每日寄语，要求简短，但是要温暖人心，或者俏皮，但一定要富有哲理或者励志，可以你自己原创，也可以引用名人名言。:格式<font color="warning"> 寄语 </font>
    """

    @classmethod
    def ai_info(cls):
        spider_config = [
            SimpleSpiderParams(
                prompt=cls.prompt
            ),
        ]
        now = datetime.datetime.now().strftime("%Y/%m/%d")
        prompt = f"""
        - 请你将上述表格汇总
        - 不要使用代码块``````包起来
        {cls.normal_prompt}
        

        # 格式如下：
        > 内容概要: <font color="comment"> xxxx </font>
        > 发表时间: <font color="comment"> xxxx </font>
        > 链接地址: <font color="comment"> [xxxx](http://xxxxx) </font>
        """
        spider = AIBotCNSpider()
        spider.run(params=spider_config)
        res = spider.summary(prompt=prompt)
        res = '<font color="warning"> 每日最新AI资讯 </font>\n' + res
        cls.send_WWXRobot(text=res)
        return res

    @classmethod
    def hf(cls):
        spider_config = [
            SimpleSpiderParams(
                url="https://huggingface.co/models",
                prompt=cls.prompt
            )
        ]
        now = datetime.datetime.now().strftime("%Y/%m/%d")
        prompt = f"""
        - 请你将上述表格汇总
        - 不要使用代码块``````包起来
        {cls.normal_prompt}
        

        # 格式如下：
        > 内容概要: <font color="comment"> xxxx </font>
        > 发表时间: <font color="comment"> xxxx </font>
        > 链接地址: <font color="comment"> [xxxx](http://xxxxx) </font>
        """
        spider = SimpleSpider()
        spider.run(params=spider_config)
        res = spider.summary(prompt=prompt)
        res = '<font color="warning"> 速览最新开源大模型 </font>\n' + res
        cls.send_WWXRobot(text=res)
        return res

    @classmethod
    def paper(cls):
        spider_config = [
            SimpleSpiderParams(
                prompt=cls.prompt
            )
        ]
        now = datetime.datetime.now().strftime("%Y/%m/%d")
        prompt = f"""
        - 请你将上述表格汇总
        - 不要使用代码块``````包起来
        - 内容摘要最好使用中文描述
        {cls.normal_prompt}
        

        # 格式如下：
        > 标题: <font color="comment"> xxxx </font>
        > 内容概要: <font color="comment"> xxxx </font>
        > 发表时间: <font color="comment"> xxxx </font>
        > 链接地址: <font color="comment"> [xxxx](http://xxxxx) </font>
        """
        spider = PagerSpider()
        spider.run(params=spider_config, system_prompt="你是一个json解析助手")
        res = spider.summary(prompt=prompt)
        res = '<font color="warning"> 速览最新论文 </font>\n' + res
        cls.send_WWXRobot(text=res)
        return res

    @classmethod
    def send_WWXRobot(cls, text):
        wwxrbt = WWXRobot(key=EnvConfig.WEIXIN_ROBOT_KEY)
        wwxrbt.send_markdown(content=text)

    @classmethod
    def all(cls):
        logger.info("开始制作")
        cls.ai_info()
        cls.hf()
        cls.paper()
        logger.info("完成推送")

    @classmethod
    def cron(cls, cron_time="07:00"):
        logger.info("等待任务")
        schedule.every().day.at(cron_time).do(cls.all)
        while True:
            schedule.run_pending()  # 运行所有到期的任务
            time.sleep(1)


if __name__ == "__main__":
    Fire(Main)
