# gpt-demo

- 提供 gpt 以及本地大模型 demo
- 简单对话聊天
- 复杂的解决方案
- vllm 私有部署方案

## demo 列表

- [x] 通用对话 chat
- [x] gpt4o_mini_chat 多模态
- [x] 企业微信 ai 资讯小助手
- [x] 知识库问答
- [x] 撰写博客助手
- [x] deepseek代码生成
- [ ] gpt4o_chat 多模态
- [ ] 羽毛球比赛识别
- [ ] 图片文档解析助手
- [ ] pdf 文档解析助手
- [ ] 医护人员诊前小护士病情收集
- [ ] 法律助手
- [ ] 文生图创意制作
- [ ] 解题小助手

## Install

```bash
pip install git+https://github.com/aigc-open/gpt-demo.git
```

# GPT 版本系列

## online chat all in one

- 所有 demo 都可以在这里全看到

```bash
python3 -m gpt_demo.chat -p 7899
```

![](docs/gpt_all_in_one.png)

## gpt4o-mini-chat

```bash
python3 -m gpt_demo.gpt4o_mini_chat -p 7899 -e examples_file.json
```

- 其中-e 可以自定义示例文件

![](docs/gpt4o-mini.png)

## gpt ai 资讯小助手(企业微信 ai 资讯小助手)

- 将企业微信 webhook key 填入环境变量中

```bash
python3 -m gpt_demo.news_spider run -p 7899
```

![](docs/ai-bot-web.png)
![](docs/ai-bot.png)

## 知识库问答

- 上传知识库
- 根据知识库近似搜索，进行 llm rag 知识库问答
- 项目依赖: https://github.com/aigc-open/llm-knowledge-function
  - 生成级别的 api 接口：xxxx

```bash
python3 -m gpt_demo.simple_knowledge_chat -p 40002
```

![](docs/simple-knowledge-chat.png)

## 博客撰写小助手

- 一键写博客
- 一键复制 markdown，方便发博客

```bash
python3 -m gpt_demo.gpt_write_blog -p 40002
```

![](docs/blog-ai.png)

## deepseek代码生成
- 代码续写
- 代码中间补全

```bash
python3 -m gpt_demo.deepseek-code -p 7899
```
![](docs/deepseek-code.png)

# VLLM 本地大模型版本系列
