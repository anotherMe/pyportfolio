import re

def is_valid_isin(isin: str) -> bool:
    s = (isin or "").strip().upper().replace(" ", "")
    if not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}\d", s):
        return False
    # Convert letters to digits: A=10 ... Z=35, and build the digit string (exclude final check digit for conversion step)
    converted = []
    for ch in s[:-1]:
        if ch.isalpha():
            converted.append(str(ord(ch) - 55))
        else:
            converted.append(ch)
    digits = "".join(converted) + s[-1]
    # Luhn algorithm (on the digits string, processing from right)
    total = 0
    rev = digits[::-1]
    for i, ch in enumerate(rev):
        d = int(ch)
        if i % 2 == 1:  # double every second digit (i=1 is the second from right)
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0