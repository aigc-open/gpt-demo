# gpt-demo


## demo列表

- [x] 通用对话chat
- [x] gpt4o-mini-chat多模态
- [ ] gpt4o-chat多模态
- [ ] vllm 本地大模型支持适配
- [ ] vllm 支持glm-4-9b-chat
- [ ] vllm 支持glm-4v-9b多模态
- [ ] 写博客助手
- [ ] 羽毛球比赛识别
- [ ] 图片文档解析助手
- [ ] pdf文档解析助手

#@ Install
```bash
pip install git+https://github.com/aigc-open/gpt-demo.git
```

#@ Run
```bash
python3 -m gpt_demo.gpt-chat -p 7899 -e examples_file.json
```

#@ gpt4o-mini-chat
```bash
python3 -m gpt_demo.gpt4o-mini-chat -p 7899 -e examples_file.json
```
![](docs/gpt4o-mini.png)
