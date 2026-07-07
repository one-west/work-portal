import re
import pandas as pd
from lib.expense.models import Row

_UNICODE_SPACES = [" ", "﻿", " ", " ", "⁠",
                   "​", "‌", "‍", "　", "­", "\t"]

def to_number(x):
    """DART/카드 API 숫자 문자열 정규화. 실패 시 None."""
    if x is None:
        return None
    s = str(x)
    for sp in _UNICODE_SPACES:
        s = s.replace(sp, "")
    s = s.replace("–", "-").replace("—", "-")  # en/em dash
    s = s.strip().replace(",", "").replace(" ", "")
    if s in ("", "-", "--"):
        return None
    neg = False
    if s and s[0] in ("△", "▲"):
        neg = True
        s = s[1:]
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    try:
        val = float(s)
    except ValueError:
        return None
    return -val if neg else val

def normalize_card_no(s):
    return "".join(ch for ch in str(s) if ch.isdigit())

def extract_cards(rows):
    seen = []
    for r in rows:
        if r.card_no not in seen:
            seen.append(r.card_no)
    return seen

def read_haewoe(path):
    return pd.read_excel(path, engine="xlrd", dtype=str)

def normalize_haewoe(df):
    rows = []
    for _, x in df.iterrows():
        rows.append(Row(
            date=str(x.get("승인일", "")).strip(),
            shop=str(x.get("가맹점명", "")).strip(),
            usd=to_number(x.get("현지이용금액")) or 0.0,
            idr=0.0,
            krw=to_number(x.get("결제원금")) or 0.0,
            user=str(x.get("이용자명", "")).strip(),
            source="haewoe",
            card_no=normalize_card_no(x.get("카드번호", "")),
        ))
    return rows
