# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this app does

사내 통합 업무 포털 — 법령검색·DART 재무제표 수집 등 업무 도구를 단일 Streamlit 멀티페이지 포털로 통합.  
배포: https://hytc-dart.streamlit.app/

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

`.env` 파일에 API 키 설정 (`.env`는 gitignore됨):
```
DART_API_KEY=...
LAW_API_KEY=...
```

Streamlit Cloud는 대시보드 Secrets에서 동일한 키를 설정.

## Testing

```bash
python -m pytest tests/          # 정산 로직(lib/expense) 단위·통합 테스트
```

`lib/expense/*`는 streamlit 비의존 순수 함수라 테스트가 가능. 템플릿 로드 시 openpyxl의 "Data Validation extension is not supported" 경고는 x14 드롭다운 관련 알려진 무해 경고.

## Directory structure

```
work-portal/
├── app.py                   # 포털 메인 랜딩 페이지 (Streamlit Cloud 진입점)
├── pages/
│   ├── 1_법령검색.py         # 국가법령정보센터 API 연동
│   ├── 2_DART재무제표.py     # OpenDART 재무제표 수집기
│   └── 3_해외출장비정산.py    # 카드내역 → 정산서 2-1 법인카드 탭 자동 작성
├── lib/expense/             # 정산 로직 (파서·규칙·라이터, streamlit 비의존)
├── templates/               # 내장 정산서 템플릿(.xlsx)
├── tests/expense/           # lib/expense 단위·통합 테스트 (pytest)
└── docs_cache/              # OpenDartReader corp_codes 캐시 (git 추적)
```

## Architecture

Streamlit 네이티브 멀티페이지 앱. `app.py`가 Streamlit Cloud 진입점이며 `pages/` 하위 파일이 자동으로 사이드바에 노출됨.

### pages/1_법령검색.py

- API: `GET http://www.law.go.kr/DRF/lawSearch.do` (params: `OC`, `target=law`, `type=XML`, `query`)
- 응답 XML `<law>` 태그 파싱 → DataFrame → `st.column_config.LinkColumn`으로 상세 링크 표시
- 상세 URL: `https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq={법령일련번호}`
- `LAW_API_KEY`: `.env` → `st.secrets` → 사이드바 입력 순

### pages/2_DART재무제표.py

주요 함수:
- `to_number_strict(x)` — DART API 반환 숫자 문자열 정규화. 유니코드 공백 11종, 삼각형(△▲) 음수, 괄호 `(n)` 음수, en/em dash 처리
- `save_excel_with_comma_format(df, file_name)` — XlsxWriter로 셀 단위 쓰기 후 openpyxl로 2차 교정, `#,##0` 서식 적용
- `init_dart(key)` — `@st.cache_resource` 래핑된 OpenDartReader 초기화 (앱 재실행 시 재초기화 방지)

수집 흐름: API 키 로드 → corp_codes 캐시 복사 → `init_dart()` → UI → 버튼 클릭 → 진행률 표시(프로그레스바 + 상태 텍스트) → `finstate_all()` → XBRL 없으면 `finstate()` fallback (CFS→OFS) → 엑셀 저장 → DataFrame 미리보기 + 다운로드 버튼

### pages/3_해외출장비정산.py

카드 매입/승인 내역 엑셀에서 특정 카드 사용분을 추출해 정산서 템플릿의 `2-1출장경비 법인카드` 탭을 자동 작성. UI(페이지)는 배선만 담당하고 로직은 `lib/expense/`(streamlit 비의존)에 분리 → `tests/expense/`로 단위·통합 테스트.

- `lib/expense/parsers.py` — `.xls` 읽기(xlrd), 카드번호 정규화, 해외매입/국내승인/카드마스터 파싱, 숫자 정규화(`to_number`)
- `lib/expense/rules.py` — 앱에서 편집 가능한 분류 규칙(원천별 분기: 해외=가맹점명 / 국내=업종명), 기본셋 `rules_default.json`, JSON 로드/저장, `classify`
- `lib/expense/writer.py` — openpyxl로 내장 템플릿 2-1 탭 채우기(행 확장·병합·`$L` 수식·합계 SUM) + 요약탭 메타/환율 기입

수집 흐름: 해외매입.xls + 국내승인.xls(둘 중 최소 1) + 카드마스터(선택) 업로드 → 카드 다중선택(마스터 라벨) → 카드별 메타표 → 분류·편집표(`st.data_editor`) → `build_settlement()` → 단일 xlsx / 다중 ZIP 다운로드.

- **L열(원화금액)**: 해외 건 = `결제원금`, 국내 건 = `승인금액`
- 요약 탭은 템플릿의 `SUMIFS` 수식이 detail 탭에서 **자동 집계**(코드가 안 건드림)
- `.xls`는 **xlrd로만** 읽음 (Streamlit Cloud 리눅스 호환, LibreOffice 불필요)
- 설계/계획 문서: `docs/superpowers/specs|plans/2026-07-07-해외출장비정산-*`

## OpenDartReader 캐시

`docs_cache/opendartreader_corp_codes_{YYYYMMDD}.pkl` 형식으로 일별 캐시. Streamlit Cloud 파일시스템은 재시작마다 초기화되므로 앱 시작 시 기존 pkl을 오늘 날짜로 복사해 재사용. 캐시가 오래되면 최신 pkl로 교체 후 커밋.

## 기업 목록 변경

`pages/2_DART재무제표.py`의 `code_name_map` dict 수정. 키는 종목코드(6자리) 또는 DART 고유번호(8자리, 비상장사).

## API 동작 특이사항

- `finstate_all()` — XBRL 기반 API. 당일 제출 보고서 또는 일부 분기 보고서는 XBRL 처리 완료 전 빈 결과 반환
- `finstate()` — non-XBRL fallback. `finstate_all()` 빈 결과 시 CFS → OFS 순으로 시도
