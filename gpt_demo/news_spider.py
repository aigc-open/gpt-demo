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


class SogouSpider(SimpleSpider):
    def request(self, url):
        query = "大模型新闻事件 绘图模型新闻事件 ai新闻事件 芯片新闻事件"
        url = f"https://www.sogou.com/web?query={query}&sourceid=inttime_day&tsn=1"
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
        html = requests.get(url,headers=headers).text

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
    - 筛选出最新的Top5的AI相关资讯,结果中不要带这句话
    - 给我写一个每日寄语，要求简短，但是要温暖人心，或者俏皮，引用名人名言。:格式<font color="warning"> 寄语 </font>
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
        res = '<font color="warning"> 昨日AI资讯 </font>\n' + res
        cls.send_WWXRobot(text=res)
        return res

    @classmethod
    def sogou(cls):
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
        - 只要{now}最近一天的数据，其他的不要

        # 格式如下：
        > 内容概要: <font color="comment"> xxxx </font>
        > 发表时间: <font color="comment"> xxxx </font>
        > 链接地址: <font color="comment"> [xxxx](http://xxxxx) </font>
        """
        spider = SogouSpider()
        spider.run(params=spider_config)
        res = spider.summary(prompt=prompt)
        res = '<font color="warning"> 最新AI实时新闻 </font>\n' + res
        cls.send_WWXRobot(text=res,key=EnvConfig.WEIXIN_ROBOT_KEY_SOGOU)
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
        res = '<font color="warning"> 昨日开源大模型 </font>\n' + res
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
        res = '<font color="warning"> 昨日AI论文 </font>\n' + res
        cls.send_WWXRobot(text=res)
        return res

    @classmethod
    def send_WWXRobot(cls, text, key=EnvConfig.WEIXIN_ROBOT_KEY):
        wwxrbt = WWXRobot(key=key)
        wwxrbt.send_markdown(content=text)

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


if __name__ == "__main__":
    Fire(Main)
