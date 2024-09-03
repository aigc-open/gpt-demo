from fire import Fire
import time
import json
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
from duckduckgo_search import DDGS


class SimpleSpiderParams(BaseModel):
    url: str = ""
    prompt: str


class SimpleSpider:
    prompt = """
    ## 数据格式为markdown
    - 请你将上面内容，解析成结构化数据
    - 请你直接返回markdown 表格数据格式，要求字段为 标题,内容概要，发表时间, 链接地址
    - 如果没有发表时间的数据，则丢弃不要
    - 链接地址如果没有域名，请直接加上
    - 如果数据中没有链接地址，则该数据丢弃
    - 链接地址请使用完整的url，请不要解析那种缩略式的链接
    - 不要使用代码块``````包起来
    {extra_prompt}

    # 格式如下：
    | 标题 | 内容概要 | 发表时间 | 链接地址 |
    | --- | --- | --- | --- |
    | xxxxx | xxxxx | 2024/08/07 09:32 | http://xxxxx |
    """
    client = OpenAI(api_key=EnvConfig.OPENAI_API_KEY,
                    base_url=EnvConfig.OPENAI_BASE_URL)
    model = EnvConfig.OPENAI_MODEL

    def chat_api(self, *args, **kwargs):
        completion = self.client.chat.completions.create(
            model=self.model,
            max_tokens=kwargs["max_length"],
            messages=kwargs["message"],
            temperature=kwargs["temperature"],
            stream=False
        )
        return completion.choices[0].message.content

    def page_to_markdown(self, data, max_length=4096, temperature=0.7):
        param = self.spider_config
        info = self.llm_data_convert(
            data=data, prompt=param.prompt, system_prompt=self.system_prompt,
            max_length=max_length, temperature=temperature)
        return info

    def markdown_to_json(self, data, max_length=4096, temperature=0.7):
        md_to_json_prompt = """
            ## markdown 数据解析为 json
            - 请你将上面内容，解析成结构化数据
            - 筛选出最新的Top10的AI相关资讯,结果中不要带这句话
            - 请你直接返回json数据格式，要求字段为 标题, 内容概要，发表时间, 链接地址
            - 如果没有发表时间的数据，则丢弃不要
            - 链接地址错误的也直接丢弃
            - 不要使用代码块``````包起来
            - 不要使用 ```json  xxxx ```包裹，直接返回json list给我
            - 没有数据直接返回 []
            - 内容概要需要很简单的描述，不要太长

            # 格式如下：
            [
                {
                    "标题": "xxx",
                    "内容概要": "xxx",
                    "发表时间": "xxx",
                    "链接地址": "xxx"
                }
            ]
            """
        info = self.llm_data_convert(
            data=data, prompt=md_to_json_prompt, system_prompt="你是一个markdown解析助手",
            max_length=max_length, temperature=temperature)
        try:
            return json.loads(info)
        except Exception as e:
            logger.warning(e)
            logger.warning(f"无法json序列化: {info}")
            return []

    def markdown_to_weixin(self, data, max_length=4096, temperature=0.7):
        weixin_robot_prompt = """
        - 请你将上述表格汇总
        - 不要使用代码块``````包起来
        - 内容摘要最好使用中文描述
        - 筛选出最新的Top10的AI相关资讯,结果中不要带这句话
        - 给我写一个每日寄语，要求简短，但是要温暖人心，或者俏皮，引用名人名言。:格式<font color="warning"> 寄语 </font>

        # 格式如下：
        > 内容概要: <font color="comment"> xxxx </font>
        > 发表时间: <font color="comment"> xxxx </font>
        > 链接地址: <font color="comment"> [xxxx](http://xxxxx) </font>
        """
        message = [{"role": "system", "content": "你是一个markdown解析助手"}, {
            "role": "system", "content": f"```{data}```"}, {"role": "user", "content": weixin_robot_prompt}]
        info = self.chat_api(
            max_length=max_length, temperature=temperature, message=message)
        return info

    def generate_warm_words(self, max_length=4096, temperature=1.4):
        message = [{"role": "system", "content": "你是一个有用的助手"}, {
            "role": "user", "content": "给我写一个每日寄语，要求简短，但是要温暖人心，或者俏皮，引用名人名言， 这个寄语要非常简单, 格式要求:   xxxx--名人"}]
        info = self.chat_api(
            max_length=max_length, temperature=temperature, message=message)
        return info

    def llm_data_convert(self, data, prompt, system_prompt="你是一个markdown解析助手", max_length=4096, temperature=0.7):
        messages = [{"role": "system", "content": system_prompt},
                    {"role": "system", "content": f"```{data}```"},
                    {"role": "user", "content": prompt}]
        print(messages)
        info = self.chat_api(
            max_length=max_length, temperature=temperature, message=messages)
        return info

    def set_config(self):
        extra_prompt = ""
        self.spider_config = SimpleSpiderParams(
            prompt=self.prompt.format(extra_prompt=extra_prompt))
        self.system_prompt = "你是一个html解析助手"

    def __init__(self):
        self.spider_results = []

    def request(self, url):
        html = requests.get(url).text
        return html

    def run(self, max_length=4096, temperature=1.4, to_weixin_robot=False):
        logger.info("开始运行...")
        self.set_config()
        param = self.spider_config
        try:
            html = self.request(url=param.url)
        except Exception as e:
            logger.exception(e)
            return []
        info_markdown = self.page_to_markdown(
            data=html, max_length=max_length, temperature=temperature)
        info_json = self.markdown_to_json(
            data=info_markdown, max_length=max_length, temperature=temperature)
        logger.info("结束")
        return info_json


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
        extra_prompt = "- 你的域名是https://huggingface.co,不要写错了"
        self.spider_config = SimpleSpiderParams(
            url="https://hf-mirror.com/models", prompt=self.prompt.format(extra_prompt=extra_prompt))
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


class AiBaseSpider(SimpleSpider):

    def set_config(self):
        extra_prompt = "- 你的域名是https://www.aibase.com/,不要写错了"
        self.spider_config = SimpleSpiderParams(
            url="https://www.aibase.com/zh/news", prompt=self.prompt.format(extra_prompt=extra_prompt))
        self.system_prompt = "你是一个html解析助手"

    def request(self, url):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        }
        html = requests.get(url, headers=headers).text

        soup = BeautifulSoup(html, 'html.parser')
        a_items = soup.find_all('a', class_="group")
        xml_str = ""
        count = 0
        for elem in a_items:
            xml_str += str(elem)
            count += 1
            if count > 15:
                break
        return xml_str


class DuckDuckGoSpider(SimpleSpider):

    def request(self, url):
        results = DDGS().text("大模型新闻事件 绘图模型新闻事件 ai新闻事件 芯片新闻事件", max_results=10,timelimit="d")
        return results


    def run(self, max_length=4096, temperature=1.4, to_weixin_robot=False):
        logger.info("开始运行...")
        self.set_config()
        param = self.spider_config
        try:
            html_json = self.request(url=param.url)
        except Exception as e:
            logger.exception(e)
            return []
        info_json = []
        for data in html_json:
            info = {
                    "标题": data["title"],
                    "内容概要": data["body"],
                    "发表时间": "最近",
                    "链接地址": data["href"],
                }
            info_json.append(info)
        logger.info("结束")
        return info_json