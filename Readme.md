# 🏢 사내 통합 업무 포털 (Streamlit Web App)

부서별 업무 도구를 단일 웹 포털로 통합한 사내 애플리케이션입니다.  
Streamlit으로 개발되어 브라우저에서 간편하게 사용 가능합니다.

#### 접속 URL : https://hytc-dart.streamlit.app/

## 🚀 제공 기능

### ⚖️ 법령 검색
✅ 국가법령정보센터 오픈 API 연동  
✅ 법령명·소관부처·시행일 조회  
✅ 상세 페이지 바로가기 링크

### 📊 DART 재무제표 수집기
✅ OpenDART API 연동  
✅ 기업·연도·보고서 유형 멀티 선택  
✅ 전체 재무제표 자동 수집  
✅ 결과 미리보기 + 엑셀 다운로드 (`#,##0` 서식)  
✅ XBRL 미추출 시 non-XBRL fallback 자동 처리

## 📦 설치 방법

Python 3.9 이상이 설치되어 있어야 합니다.

```bash
pip install -r requirements.txt
```

## ▶️ 사용 방법

`.env` 파일에 API 키 설정:
```
DART_API_KEY=발급받은_DART_API_키
LAW_API_KEY=발급받은_법령_API_키
```

```bash
streamlit run app.py
```

## 🔑 API 키 발급

| 서비스 | 발급처 |
| ------ | ------ |
| DART API | https://opendart.fss.or.kr |
| 법령 API | https://www.law.go.kr/LSW/openApi.do |

## 📑 지원 보고서 유형 (DART)

| 유형        | 코드  |
| ----------- | ----- |
| 사업보고서  | 11011 |
| 반기보고서  | 11012 |
| 3분기보고서 | 11014 |
| 1분기보고서 | 11013 |

## 📋 패치 내역

### v0.4.0
- **feat**: 사내 통합 업무 포털로 확장 (멀티페이지 구조)
- **feat**: 법령 검색 페이지 추가 — 국가법령정보센터 API 연동
- **fix**: Streamlit Cloud 초기화 타임아웃 해결 — corp_codes 캐시 재사용 + `@st.cache_resource`

### v0.3.0
- **feat**: 거래처 추가 — 에스케이온, 한솔아이원스, 나래나노텍 (총 14개사)
- **fix**: `finstate_all()` XBRL 미추출 시 `finstate()` fallback 추가
- **fix**: 숫자 데이터 변환 강화 — 유니코드 특수공백·삼각형 음수(△▲)·괄호 음수 처리
- **feat**: 엑셀 출력 개선 — XlsxWriter + openpyxl 2차 교정, `#,##0` 서식 자동 적용
- **feat**: 연도 선택 범위 동적화 — 현재 연도 기준 최근 10년 자동 생성
