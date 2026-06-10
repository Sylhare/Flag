#!/usr/bin/env python3
"""Recover the flags embedded in the NSIS-installer reverse challenges
(re_challenge1.exe / re_challenge2.exe) from NSEC 2019.

re_challenge1.exe stores the flag as a plain string in the NSIS strings block.
re_challenge2.exe builds the flag one character at a time with StrCpy
(EW_ASSIGNVAR) entries that prepend/append a single character to a variable;
we replay those entries to reconstruct the flag.

Run on the .exe files directly:  python3 solve_nsis.py
"""
import zlib
import struct
import re
import sys

# Offset of the deflate-compressed NSIS header inside these specific installers
HDR_OFFSET = 36384


def inflate_header(path):
    data = open(path, "rb").read()
    return zlib.decompressobj(-15).decompress(data[HDR_OFFSET:])


def parse_blocks(out):
    # NSIS header: int flags, then 8 block_header {int offset; int num}
    return [struct.unpack("<II", out[4 + i * 8:4 + i * 8 + 8]) for i in range(8)]


def solve_plaintext(path):
    out = inflate_header(path)
    m = re.search(rb"FLAG-[0-9a-fA-F]{40}", out)
    return m.group().decode() if m else None


def solve_assembled(path):
    out = inflate_header(path)
    blocks = parse_blocks(out)
    ent_off, ent_num = blocks[2]          # ENTRIES block
    str_off = blocks[3][0]                # STRINGS block
    strblk = out[str_off:blocks[4][0]]

    def getstr(idx):
        # Decode a NSIS string: bytes 0x01/0x02/0x03 introduce 3-byte
        # variable/shell/registry references; everything else is a literal char.
        raw = strblk[idx:strblk.find(b"\x00", idx)]
        toks, i = [], 0
        while i < len(raw):
            b = raw[i]
            if b in (1, 2, 3):
                toks.append(("VAR",)); i += 3
            else:
                toks.append(chr(b)); i += 1
        return toks

    entries = [struct.unpack("<7I", out[ent_off + i * 28:ent_off + i * 28 + 28])
               for i in range(ent_num)]

    flag = ""
    for cmd, *p in entries:
        if cmd != 25:                     # EW_ASSIGNVAR (StrCpy)
            continue
        s = getstr(p[1])                  # source string: one literal + one VAR ref
        lit = "".join(c for c in s if c != ("VAR",))
        varpos = [j for j, c in enumerate(s) if c == ("VAR",)]
        if not lit or not varpos:
            continue
        if varpos[0] == 0:
            flag += lit                   # "{VAR}X" -> append
        else:
            flag = lit + flag             # "X{VAR}" -> prepend
    m = re.search(r"FLAG-[0-9a-fA-F]{40}", flag)
    return m.group() if m else flag


if __name__ == "__main__":
    print("re_challenge1.exe:", solve_plaintext("re_challenge1.exe"))
    print("re_challenge2.exe:", solve_assembled("re_challenge2.exe"))
