from dataclasses import dataclass

@dataclass
class Row:
    date: str
    shop: str
    usd: float
    idr: float
    krw: float
    user: str
    source: str          # "haewoe" | "gukne"
    card_no: str
    industry: str = ""   # 업종명 (국내 건만)
    category: str = ""   # D열 분류 결과/편집값
    detail: str = ""     # F열 상세내역

@dataclass
class Meta:
    traveler: str = ""
    start_date: str = ""
    end_date: str = ""
    region: str = ""
    purpose: str = ""
    usd_rate: float = 0.0
    idr_rate: float = 0.0

@dataclass
class CardInfo:
    card_no: str
    traveler: str = ""
    region: str = ""
    label: str = ""      # 용도 라벨 (예: 해외출장4)
