### Pulled from resolveurl for a scraper that uses it.

import re
import sys
import codecs


def decodeSalt(e):
    t = ""
    for c in e:
        t += str(ord(c) - 100)
    return t


def test(e):
    return True if re.search(r'_juicycodes\(', e, re.IGNORECASE) else False


def run(code):
    try:
        symbolMap = ["`", "%", "-", "+", "*", "$", "!", "_", "^", "="]
        code = re.findall(r'_juicycodes\(([^\)]+)', code, re.IGNORECASE)[0]
        code = eval(code)
        ordSalt = decodeSalt(code[-3:])
        jscode = code[:-3]
        x = (len(jscode) + 3) % 4
        jscode = jscode + "==="
        jscode = jscode[:-x]
        jscode = jscode.replace("_", "+").replace("-", "/")
        jscode = codecs.decode(jscode.encode('ascii'), 'base64')
        obfuscated = codecs.decode(jscode.decode('ascii'), 'rot13')
        ordString = ""
        for c in obfuscated:
            ordString += str(symbolMap.index(c))
        splittedOrd = [ordString[i:i + 4] for i in range(0, len(ordString), 4)]
        deobfuscated = ""
        for c in splittedOrd:
            c = int(c) % 1000 - int(ordSalt)
            deobfuscated += chr(c)
        return deobfuscated
    except:
        return None


