from duckduckgo_search import DDGS
results = DDGS().text("大模型新闻事件 绘图模型新闻事件 ai新闻事件 芯片新闻事件", max_results=10,timelimit="d")

print(results)