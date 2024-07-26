simbol = "-"*100

simple_examples = ""
simple_examples = simple_examples + """
你好，你是谁呢
""" + simbol

simple_examples = simple_examples + """
## 你是一个数学老师，请你详细解答以下题目，要求如下：
- 所有的数学公式请按如下格式返回: 
$$
c^2 = a^2 + b^2
$$

## 问题
- 爷爷有16%的糖水50克，（1）要把它稀释成10%的糖水，需加水多少克？（2）若要把它变成30%的糖水，需加糖多少克？
""" + simbol

simple_examples = simple_examples + """
it is a sheep. (改为复数句子)
""" + simbol

simple_examples = simple_examples + """
假设我将采访李白，根据我的一个问题，帮我扩展出10个问题，最好给我展示成python的list格式 - 格式如下: question=[]
""" + simbol

simple_examples = simple_examples + """
下列关于力的说法中，正确的是(   ) 
A、分力必小于合力
B、物体受几个力作用时，运动状态一定发生改变 
C、重力的施力物体是地球
D、滑动摩擦力一定对物体做负功，使物体的机械能减少
""" + simbol

simple_examples = simple_examples + """
请你写一个python代码呢关于fastapi
""" + simbol


class Examples:

    @classmethod
    def simple_chat(cls):
        out = []
        for data in simple_examples.split(simbol):
            if data.strip():
                out.append([data.strip()])
        return out
