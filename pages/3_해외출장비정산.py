# pages/3_해외출장비정산.py
import io
import zipfile
import pandas as pd
import streamlit as st
from lib import expense


def _num(x, default):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return default if v != v else v   # NaN check (v != v is True for NaN)


def _txt(x):
    if x is None:
        return ""
    s = str(x)
    return "" if s.lower() == "nan" else s


st.set_page_config(page_title="해외출장비 정산", layout="wide")
st.title("해외출장비 정산서 자동 작성")

st.markdown("카드 매입/승인 내역과 카드 마스터를 올리면 **2-1 법인카드 탭**을 채운 정산서를 생성합니다.")

# ── 1) 업로드 ──
st.caption("⬆️ 각 영역에 파일을 **끌어다 놓거나(드래그앤드롭)** **Upload 버튼**으로 선택할 수 있습니다.")
_DND_HELP = "파일을 이 영역으로 드래그앤드롭하거나 Upload 버튼으로 선택하세요."
c1, c2, c3 = st.columns(3)
f_haewoe = c1.file_uploader("해외매입내역 (.xls) — 클릭 또는 드래그앤드롭", type=["xls"], help=_DND_HELP)
f_gukne = c2.file_uploader("국내승인내역 (.xls, 선택) — 클릭 또는 드래그앤드롭", type=["xls"], help=_DND_HELP)
f_master = c3.file_uploader("카드 마스터 (.xls/.xlsx/.csv) — 클릭 또는 드래그앤드롭", type=["xls", "xlsx", "csv"], help=_DND_HELP)

if not f_haewoe and not f_gukne:
    st.info("해외매입 또는 국내승인 중 최소 하나를 업로드하세요.")
    st.stop()

# ── 2) 파싱 ──
try:
    rows = []
    if f_haewoe:
        rows += expense.normalize_haewoe(pd.read_excel(f_haewoe, engine="xlrd", dtype=str))
    if f_gukne:
        rows += expense.normalize_gukne(pd.read_excel(f_gukne, engine="xlrd", dtype=str))

    master = {}
    if f_master:
        _mname = (getattr(f_master, "name", "") or "").lower()
        if _mname.endswith(".csv"):
            _mdf = pd.read_csv(f_master, dtype=str)
        elif _mname.endswith(".xls"):
            _mdf = pd.read_excel(f_master, engine="xlrd", dtype=str)
        else:
            _mdf = pd.read_excel(f_master, dtype=str)
        master = expense.parse_card_master(_mdf)
except Exception as e:
    st.error(f"업로드 파일을 읽는 중 오류: {e}")
    st.stop()

# ── 3) 규칙 (세션 + 다운/업) ──
with st.expander("분류 규칙 편집"):
    up = st.file_uploader("규칙 JSON 업로드", type=["json"], key="rules_up")
    if up:
        st.session_state["rules"] = expense.load_rules(up.getvalue().decode("utf-8"))
    if "rules" not in st.session_state:
        st.session_state["rules"] = expense.default_rules()
    rules_df = pd.DataFrame([r.__dict__ for r in st.session_state["rules"]])
    edited = st.data_editor(rules_df, num_rows="dynamic", use_container_width=True,
                            column_config={"category": st.column_config.SelectboxColumn(
                                options=[""] + expense.CATEGORIES)})
    _valid_rules = []
    _dropped = 0
    for r in edited.to_dict("records"):
        kw = r.get("keyword")
        order = r.get("order")
        match = r.get("match")
        if kw is None or (isinstance(kw, float) and kw != kw) or str(kw).strip() == "":
            _dropped += 1
            continue
        if order is None or (isinstance(order, float) and order != order):
            _dropped += 1
            continue
        if match not in ("contains", "regex"):
            _dropped += 1
            continue
        try:
            order = int(order)
        except (TypeError, ValueError):
            _dropped += 1
            continue
        r = dict(r)
        r["order"] = order
        r["keyword"] = str(kw)
        r["category"] = _txt(r.get("category"))
        r["applies_to"] = _txt(r.get("applies_to"))
        r["note"] = _txt(r.get("note"))
        r["match"] = str(match)
        _valid_rules.append(expense.Rule(**r))
    if _dropped:
        st.caption(f"불완전한 규칙 {_dropped}건은 무시되었습니다.")
    st.session_state["rules"] = _valid_rules
    import json
    st.download_button("규칙 JSON 다운로드",
                       data=json.dumps(expense.dump_rules(st.session_state["rules"]),
                                       ensure_ascii=False, indent=2),
                       file_name="expense_rules.json")

rules = st.session_state["rules"]

# ── 4) 카드 다중선택 (마스터 라벨) ──
def _fmt_card_no(card):
    if card.isdigit() and len(card) >= 8:
        return "-".join(card[i:i + 4] for i in range(0, len(card), 4))
    return card

def label(card):
    """카드번호 / 용도 / 출장자명 / 지역 — 빈 값은 '-'."""
    info = master.get(card)
    용도 = (info.label if info else "") or "-"
    출장자 = (info.traveler if info else "") or "-"
    지역 = (info.region if info else "") or "-"
    return f"{_fmt_card_no(card)} / {용도} / {출장자} / {지역}"

cards = expense.extract_cards(rows)
picked = st.multiselect("정산할 카드 선택", options=cards, format_func=label)
if not picked:
    st.stop()

# ── 5) 카드별 메타 입력표 (마스터 프리필) ──
st.subheader("카드별 출장 정보")
meta_rows = []
for card in picked:
    info = master.get(card, expense.CardInfo(card_no=card))
    meta_rows.append({"카드": label(card), "card_no": card, "출장자": info.traveler,
                      "기간시작": "", "기간종료": "", "지역": info.region, "목적": "",
                      "USD환율": 1470.0, "IDR환율": 0.09})
meta_df = st.data_editor(pd.DataFrame(meta_rows), use_container_width=True,
                         column_config={"card_no": None}, hide_index=True)

# ── 6) 카드별 편집표 + 생성 ──
files = {}
for _, mrow in meta_df.iterrows():
    card = mrow["card_no"]
    crows = expense.filter_and_sort(rows, card)
    crows = expense.classify_rows(crows, rules)
    traveler = _txt(mrow["출장자"])
    for r in crows:
        if traveler:
            r.user = traveler
        elif not r.user:
            r.user = "공용"
    st.markdown(f"**{label(card)}** — {len(crows)}건")
    detail_df = pd.DataFrame([{"날짜": r.date, "상호": r.shop, "항목": r.category,
                               "상세내역": r.detail, "USD": r.usd, "원화": r.krw,
                               "사용자": r.user} for r in crows])
    edited_detail = st.data_editor(detail_df, use_container_width=True, hide_index=True,
                                   key=f"detail_{card}",
                                   disabled=["날짜", "상호", "USD", "원화"],
                                   column_config={"항목": st.column_config.SelectboxColumn(
                                       options=[""] + expense.CATEGORIES)})
    # 편집 반영
    for r, (_, d) in zip(crows, edited_detail.iterrows()):
        r.category, r.detail, r.user = d["항목"], d["상세내역"], d["사용자"]
    meta = expense.Meta(traveler=traveler, start_date=_txt(mrow["기간시작"]),
                        end_date=_txt(mrow["기간종료"]), region=_txt(mrow["지역"]),
                        purpose=_txt(mrow["목적"]), usd_rate=_num(mrow["USD환율"], 1470.0),
                        idr_rate=_num(mrow["IDR환율"], 0.09))
    try:
        files[card] = (traveler or card, expense.build_settlement(crows, meta))
    except Exception as e:
        st.error(f"'{label(card)}' 정산서 생성 실패: {e}")
        continue

# ── 7) 다운로드 (단일=xlsx, 다중=ZIP) ──
st.subheader("다운로드")
if not files:
    st.warning("생성된 정산서가 없습니다.")
    st.stop()
if len(files) == 1:
    name, data = next(iter(files.values()))
    st.download_button(f"정산서 다운로드 ({name})", data=data,
                       file_name=f"해외출장비 정산서_{name}.xlsx")
else:
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w") as zf:
        for card, (name, data) in files.items():
            zf.writestr(f"해외출장비 정산서_{name}_{card[-4:]}.xlsx", data)
    st.download_button("정산서 전체 ZIP 다운로드", data=zbuf.getvalue(),
                       file_name="해외출장비 정산서_일괄.zip")
