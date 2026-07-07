# pages/3_해외출장비정산.py
import io
import zipfile
import pandas as pd
import streamlit as st
from lib import expense

st.set_page_config(page_title="해외출장비 정산", layout="wide")
st.title("해외출장비 정산서 자동 작성")

st.markdown("카드 매입/승인 내역과 카드 마스터를 올리면 **2-1 법인카드 탭**을 채운 정산서를 생성합니다.")

# ── 1) 업로드 ──
c1, c2, c3 = st.columns(3)
f_haewoe = c1.file_uploader("해외매입내역 (.xls)", type=["xls"])
f_gukne = c2.file_uploader("국내승인내역 (.xls, 선택)", type=["xls"])
f_master = c3.file_uploader("카드 마스터 (.xls/.xlsx/.csv)", type=["xls", "xlsx", "csv"])

if not f_haewoe and not f_gukne:
    st.info("해외매입 또는 국내승인 중 최소 하나를 업로드하세요.")
    st.stop()

# ── 2) 파싱 ──
rows = []
if f_haewoe:
    rows += expense.normalize_haewoe(pd.read_excel(f_haewoe, engine="xlrd", dtype=str))
if f_gukne:
    rows += expense.normalize_gukne(pd.read_excel(f_gukne, engine="xlrd", dtype=str))

master = {}
if f_master:
    master = expense.parse_card_master(expense.read_card_master(f_master))

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
    st.session_state["rules"] = [expense.Rule(**r) for r in edited.to_dict("records")]
    import json
    st.download_button("규칙 JSON 다운로드",
                       data=json.dumps(expense.dump_rules(st.session_state["rules"]),
                                       ensure_ascii=False, indent=2),
                       file_name="expense_rules.json")

rules = st.session_state["rules"]

# ── 4) 카드 다중선택 (마스터 라벨) ──
def label(card):
    info = master.get(card)
    if info and (info.label or info.traveler):
        return f"{info.label} · {info.traveler} · {info.region} ({card[-4:]})".strip(" ·")
    return card

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
    for r in crows:
        if not r.user or r.user == "공용":
            r.user = mrow["출장자"] or "공용"
    st.markdown(f"**{label(card)}** — {len(crows)}건")
    detail_df = pd.DataFrame([{"날짜": r.date, "상호": r.shop, "항목": r.category,
                               "상세내역": r.detail, "USD": r.usd, "원화": r.krw,
                               "사용자": r.user} for r in crows])
    edited_detail = st.data_editor(detail_df, use_container_width=True, hide_index=True,
                                   key=f"detail_{card}",
                                   column_config={"항목": st.column_config.SelectboxColumn(
                                       options=[""] + expense.CATEGORIES)})
    # 편집 반영
    for r, (_, d) in zip(crows, edited_detail.iterrows()):
        r.category, r.detail, r.user = d["항목"], d["상세내역"], d["사용자"]
    meta = expense.Meta(traveler=mrow["출장자"], start_date=str(mrow["기간시작"]),
                        end_date=str(mrow["기간종료"]), region=mrow["지역"],
                        purpose=mrow["목적"], usd_rate=float(mrow["USD환율"]),
                        idr_rate=float(mrow["IDR환율"]))
    files[card] = (mrow["출장자"] or card, expense.build_settlement(crows, meta))

# ── 7) 다운로드 (단일=xlsx, 다중=ZIP) ──
st.subheader("다운로드")
if len(files) == 1:
    name, data = next(iter(files.values()))
    st.download_button(f"정산서 다운로드 ({name})", data=data,
                       file_name=f"해외출장비 정산서_{name}.xlsx")
else:
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w") as zf:
        for card, (name, data) in files.items():
            zf.writestr(f"해외출장비 정산서_{name}.xlsx", data)
    st.download_button("정산서 전체 ZIP 다운로드", data=zbuf.getvalue(),
                       file_name="해외출장비 정산서_일괄.zip")
