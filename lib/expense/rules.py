import json
import os
from dataclasses import dataclass, asdict

CATEGORIES = [
    "식비", "렌터카", "생필품", "소모품비", "여비교통비", "숙박비", "수수료",
    "의약품 외", "회식비", "접대비", "통신비", "기타", "항공료",
]

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "rules_default.json")

@dataclass
class Rule:
    order: int
    match: str          # "contains" | "regex"
    keyword: str
    category: str
    applies_to: str     # "haewoe" | "gukne" | "common"
    note: str = ""

def load_rules(obj):
    data = json.loads(obj) if isinstance(obj, str) else obj
    rules = [Rule(**r) for r in data["rules"]]
    return sorted(rules, key=lambda r: r.order)

def dump_rules(rules):
    return {"version": 1, "rules": [asdict(r) for r in rules]}

def default_rules():
    with open(_DEFAULT_PATH, encoding="utf-8") as f:
        return load_rules(f.read())

def validate_category(cat):
    return cat == "" or cat in CATEGORIES
