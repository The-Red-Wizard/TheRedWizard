# -*- coding: utf-8 -*-

from six.moves.urllib_parse import unquote

ALPHABET = {
    '47ab07f9': 'A', '47ab07fa': 'B', '47ab07fb': 'C', '47ab07fc': 'D', '47ab07fd': 'E',
    '47ab07fe': 'F', '47ab07ff': 'G', '47ab0800': 'H', '47ab0801': 'I', '47ab0802': 'J',
    '47ab0803': 'K', '47ab0804': 'L', '47ab0805': 'M', '47ab0806': 'N', '47ab0807': 'O',
    '47ab0808': 'P', '47ab0809': 'Q', '47ab080a': 'R', '47ab080b': 'S', '47ab080c': 'T',
    '47ab080d': 'U', '47ab080e': 'V', '47ab080f': 'W', '47ab0810': 'X', '47ab0811': 'Y',
    '47ab0812': 'Z',
    '47ab0819': 'a', '47ab081a': 'b', '47ab081b': 'c', '47ab081c': 'd', '47ab081d': 'e',
    '47ab081e': 'f', '47ab081f': 'g', '47ab0820': 'h', '47ab0821': 'i', '47ab0822': 'j',
    '47ab0823': 'k', '47ab0824': 'l', '47ab0825': 'm', '47ab0826': 'n', '47ab0827': 'o',
    '47ab0828': 'p', '47ab0829': 'q', '47ab082a': 'r', '47ab082b': 's', '47ab082c': 't',
    '47ab082d': 'u', '47ab082e': 'v', '47ab082f': 'w', '47ab0830': 'x', '47ab0831': 'y',
    '47ab0832': 'z',
    '47ab07e8': '0', '47ab07e9': '1', '47ab07ea': '2', '47ab07eb': '3', '47ab07ec': '4',
    '47ab07ed': '5', '47ab07ee': '6', '47ab07ef': '7', '47ab07f0': '8', '47ab07f1': '9',
    '47ab07f2': ':', '47ab07e7': '/', '47ab07e6': '.', '47ab0817': '_', '47ab07e5': '-'
}

CHARACTER_MAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def decode(uri):
    for key in ALPHABET.keys():
        uri = uri.replace(key, ALPHABET[key])
    #Added a ghetto dash replace to retain any dash thats meant to be there.(doesnt matter tho from my tests.)
    return uri.replace('---', '-$DASH$-').replace('-', '').replace('$DASH$', '-')


def decipher(encrypted_url: str):
    s1, s2 = encrypted_url[:9], encrypted_url[9:].strip('=')
    crypto = 0
    decrypted = ""
    for index, character in enumerate(s2, 1):
        crypto <<= 6
        if character in CHARACTER_MAP:
            crypto |= CHARACTER_MAP.index(character)
        if index and not (index % 4):
            decrypted, crypto = decrypted + chr((0xff0000 & crypto) >> 16) + chr((0xff00 & crypto) >> 8) + chr(0xff & crypto), 0
    if index % 4 and not (index % 2):
        crypto >>= 4
        decrypted += chr(crypto)
    if index % 4 and not (index % 3):
        decrypted += chr((65280 & crypto) >> 8) + chr(255 & crypto)
    decrypted = unquote(decrypted)
    mapper = {byte_index: byte_index for byte_index in range(0x100)}
    xcrypto = 0
    for byte_index in range(0x100):
        xcrypto = (xcrypto + mapper.get(byte_index) + ord(s1[byte_index % len(s1)])) % 0x100
        mapper[byte_index], mapper[xcrypto] = mapper[xcrypto], mapper[byte_index]
    xcryptoz, xcryptoy = 0, 0
    cipher = ""
    for character in decrypted:
        xcryptoy = (xcryptoy + 1) % 0x100
        xcryptoz = (xcryptoz + mapper.get(xcryptoy)) % 0x100
        mapper[xcryptoy], mapper[xcryptoz] = mapper[xcryptoz], mapper[xcryptoy]
        cipher += chr(ord(character) ^ mapper[(mapper[xcryptoy] + mapper[xcryptoz]) % 0x100])
    return cipher


