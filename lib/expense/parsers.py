import re
import pandas as pd
from lib.expense.models import Row, CardInfo

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

def read_gukne(path):
    return pd.read_excel(path, engine="xlrd", dtype=str)

def _is_cancelled(x):
    for col in ("상태", "승인구분"):
        v = str(x.get(col, ""))
        if "취소" in v or "거절" in v:
            return True
    return False

def normalize_gukne(df):
    rows = []
    for _, x in df.iterrows():
        if _is_cancelled(x):
            continue
        rows.append(Row(
            date=str(x.get("승인일", "")).strip(),
            shop=str(x.get("가맹점명", "")).strip(),
            usd=0.0,
            idr=0.0,
            krw=to_number(x.get("승인금액")) or 0.0,
            user=str(x.get("이용자명", "")).strip(),
            source="gukne",
            card_no=normalize_card_no(x.get("카드번호", "")),
            industry=str(x.get("업종명", "")).strip(),
        ))
    return rows

def _find_col(df, keywords):
    for c in df.columns:
        name = str(c)
        if any(k in name for k in keywords):
            return c
    return None

def read_card_master(path):
    p = str(path).lower()
    if p.endswith(".csv"):
        return pd.read_csv(path, dtype=str)
    if p.endswith(".xls"):
        return pd.read_excel(path, engine="xlrd", dtype=str)
    return pd.read_excel(path, dtype=str)

def parse_card_master(df):
    col_card = _find_col(df, ["카드번호"])
    col_name = _find_col(df, ["출장자", "이름", "성명"])
    col_region = _find_col(df, ["지역", "출장지"])
    col_label = _find_col(df, ["용도", "비고", "구분"])
    out = {}
    if col_card is None:
        return out
    for _, x in df.iterrows():
        key = normalize_card_no(x.get(col_card, ""))
        if not key:
            continue
        out[key] = CardInfo(
            card_no=key,
            traveler=str(x.get(col_name, "")).strip() if col_name else "",
            region=str(x.get(col_region, "")).strip() if col_region else "",
            label=str(x.get(col_label, "")).strip() if col_label else "",
        )
    return out

def filter_and_sort(rows, card_no):
    subset = [r for r in rows if r.card_no == card_no]
    return sorted(subset, key=lambda r: r.date)
