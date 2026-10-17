"""Byte length of a Korean string once encoded for the game (Hangul / full-width = 2, space / newline / %s = 1 each byte)."""
import re


def blen(s):
    n = 0
    for part in re.split(r'(%[0-9]*[sd])', s):
        if part.startswith('%') and len(part) > 1:
            n += len(part); continue
        for c in part:
            n += 1 if c in ' \n' else 2
    return n


if __name__ == '__main__':
    import sys
    print(blen(sys.argv[1]))
