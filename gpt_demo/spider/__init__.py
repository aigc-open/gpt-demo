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


prompt = """
## 数据格式为markdown
- 请你将上面内容，解析成结构化数据
- 请你直接返回markdown 表格数据格式，要求字段为 标题,内容概要，发表时间, 链接地址
- 如果没有发表时间的数据，则丢弃不要
- 链接地址如果没有域名，请直接加上
- 如果数据中没有链接地址，则该数据丢弃
- 不要使用代码块``````包起来

# 格式如下：
| 标题 | 内容概要 | 发表时间 | 链接地址 |
| --- | --- | --- | --- |
| xxxxx | xxxxx | 2024/08/07 09:32 | [xxxx](http://xxxxx) |
"""

weixin_robot_prompt = """
- 请你将上述表格汇总
- 不要使用代码块``````包起来
- 内容摘要最好使用中文描述
- 筛选出最新的Top5的AI相关资讯,结果中不要带这句话
- 给我写一个每日寄语，要求简短，但是要温暖人心，或者俏皮，引用名人名言。:格式<font color="warning"> 寄语 </font>

# 格式如下：
> 内容概要: <font color="comment"> xxxx </font>
> 发表时间: <font color="comment"> xxxx </font>
> 链接地址: <font color="comment"> [xxxx](http://xxxxx) </font>
"""


class NewsResponse(BaseModel):
    info_markdown: str = ""
    info_weixin: str = ""


class SimpleSpider:
    client = OpenAI(api_key=EnvConfig.OPENAI_API_KEY,
                    base_url=EnvConfig.OPENAI_BASE_URL)
    model = EnvConfig.OPENAI_MODEL

    def set_config(self):
        self.spider_config = SimpleSpiderParams(prompt=prompt)
        self.system_prompt = "你是一个html解析助手"

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

    def run(self, max_length=4096, temperature=0.7, to_weixin_robot=False):
        self.set_config()
        response = NewsResponse()
        param = self.spider_config
        try:
            html = self.request(url=param.url)
        except Exception as e:
            logger.exception(e)
            return response
        message = [{"role": "system", "content": self.system_prompt}, {
            "role": "system", "content": f"```{html}```"}, {"role": "user", "content": param.prompt}]
        info_markdown = self.chat_api(
            max_length=max_length, temperature=temperature, message=message)
        response.info_markdown = info_markdown
        if to_weixin_robot:
            message = [{"role": "system", "content": "你是一个markdown解析助手"}, {
                "role": "system", "content": f"```{info_markdown}```"}, {"role": "user", "content": weixin_robot_prompt}]
            info_weixin = self.chat_api(
                max_length=max_length, temperature=temperature, message=message)
            response.info_weixin = info_weixin
        return response


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


class SogouSpider(SimpleSpider):
    sogou_config = "query=大模型新闻事件 绘图模型新闻事件 ai新闻事件 芯片新闻事件&sourceid=inttime_day&tsn=1"

    def request(self, url):
        url = f"https://www.sogou.com/web?{self.sogou_config}"
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://www.sogou.com/web?query=%E5%A4%A7%E6%A8%A1%E5%9E%8B%E6%96%B0%E9%97%BB%E4%BA%8B%E4%BB%B6+%E7%BB%98%E5%9B%BE%E6%A8%A1%E5%9E%8B%E6%96%B0%E9%97%BB%E4%BA%8B%E4%BB%B6+ai%E6%96%B0%E9%97%BB%E4%BA%8B%E4%BB%B6+%E8%8A%AF%E7%89%87%E6%96%B0%E9%97%BB%E4%BA%8B%E4%BB%B6&_ast=1723082430&_asf=www.sogou.com&w=01029901&cid=&s_from=result_up&sut=12334&sst0=1723082491865&lkt=0%2C0%2C0&sugsuv=00302F6AABD4EB6F66B037B6D51AA965&sugtime=1723082491865',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Cookie': 'IPLOC=CN5101; SUID=6FEBD4ABC254A20B0000000066B03757; SUV=00302F6AABD4EB6F66B037B6D51AA965; SNUID=098DB2CE656378803B4068966610E314; cuid=AAE2C/jWTQAAAAuiUm+4OAEASQU; browerV=3; osV=1; ariaDefaultTheme=undefined; sw_uuid=4395856612; sg_uuid=5119021488; ABTEST=0|1723082335|v17; sst0=865; LSTMV=776%2C117; LCLKINT=706',
            'Host': 'www.sogou.com'
        }
        html = requests.get(url, headers=headers).text

        soup = BeautifulSoup(html, 'html.parser')
        news_items = soup.find_all('div', class_='results')
        xml_str = ""
        count = 0
        for elem in news_items:
            xml_str += str(elem)
            count += 1
            if count > 7:
                break
        return xml_str


class HuggingfaceSpider(SimpleSpider):

    def set_config(self):
        self.spider_config = SimpleSpiderParams(
            url="https://huggingface.co/models", prompt=prompt)
        self.system_prompt = "你是一个html解析助手"

    def request(self, url):
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        news_items = soup.find_all('article', class_='overview-card-wrapper')
        xml_str = ""
        count = 0
        for elem in news_items:
            xml_str += str(elem)
            count += 1
            if count > 7:
                break
        return xml_str
