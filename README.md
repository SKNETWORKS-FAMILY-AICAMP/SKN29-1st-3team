# 정책 뉴스에 따른 전기차 등록 대수 상관관계 분석 프로젝트
> 📅 **기간**: 2026.03.27 ~ 2026.03.31

---
## 🗂️ 프로젝트 개요
본 프로젝트는 정책 뉴스와 전기차 등록 대수 간의 관계를 분석하기 위해,
크롤링 및 API를 활용해 데이터를 수집하고 MySQL과 연동하여 Streamlit 기반의 데이터 시각화를 구현한 프로젝트입니다. 

<br>

---
## 💡 프로젝트 목표
- 크롤링과 공공데이터 API를 통한 데이터 수집
- MySQL DB 구축 및 연동
- Streamlit 기반 시각화
- 정책 뉴스량과 월별 전기차 신규 등록 대수의 상관관계 분석

<br>

---
## 📌 문제 정의
> **"전기차 수요는 정책에 의해 실제로 영향을 받을까?"**

국내 전기차 시장은 2021년 이후 급격히 성장했지만, 이 성장이 기술 발전인지 정책 효과 때문인지 명확하지 않다.
본 프로젝트는 정책 뉴스량과 월별 신규 등록 대수를 비교하여 정책이 소비자 행동에 어떤 영향을 미치는지 분석한다.

<br>

## 💡 시스템 목표
&nbsp;&nbsp;&nbsp;&nbsp;① 정책 뉴스량과 전기차 등록 데이터 시계열 비교  
&nbsp;&nbsp;&nbsp;&nbsp;② 구매자 특성 기반 정책 반응 집단 분석  
&nbsp;&nbsp;&nbsp;&nbsp;③ 정책 정보 통합 대시보드 구축  

<br>

---
## 📝 시스템 개요
```
  데이터 수집                   DB 저장                 시각화
──────────────────         ──────────         ──────────────────
공공데이터 API        ──→                          Streamlit
네이버 뉴스 크롤링     ──→      MySQL (DB)   ──→    (차트 / 표 / FAQ
기아·현대·테슬라      ──→                           / 워드클라우드)
mcee.go.kr 크롤링   ──→
```

<br>

---
## 🔧 기술 스택
 
| 구분 | 기술 |
|---|---|
| 언어 | Python |
| 데이터베이스 | MySQL |
| 시각화 | Streamlit, Plotly |
| 데이터 수집 | requests, BeautifulSoup, 공공데이터 API |
| 환경 관리 | python-dotenv |

<br>

---
## 🔍 핵심 기능
 
| 기능 | 설명 |
|---|---|
| 📈 정책 뉴스 · 전기차 등록 대수 상관관계 시각화 | 월별 전기차 등록 대수와 정책 뉴스량을 이중축으로 비교, 주요 정책 발표 시점을 마커로 표시 |
| 📋 정책 보도자료 조회 | 기후에너지환경부 보도자료를 실시간으로 불러와 정책 흐름을 한눈에 확인 |
| 👤 구매자 프로파일 분석 | 성별 · 연령대 · 차종 교차분석으로 정책에 반응한 구매 집단 파악 |
| ❓ 전기차 FAQ | 브랜드 · 카테고리 · 키워드 검색으로 전기차 관련 궁금증 해결 |
| ☁️ 뉴스 워드클라우드 | 기후에너지환경부 보도자료에서 가장 많이 언급된 키워드를 시각화 |
 
> **"뉴스 · 등록 통계 · 구매자 데이터 · 정책 보도자료까지, 흩어진 전기차 정보를 하나의 대시보드로 연결했습니다."**

<br>

---
## 🏷️ 활용 데이터
| 데이터 | 출처 | 활용 목적 |
|---|---|---|
| 자동차 신규등록정보 | 공공데이터 포털 (한국교통안전공단) | 등록자의 성별 · 나이 · 차종 · 날짜를 수집하여 차트와 표로 표시 |
| 정책 보도자료 | 기후에너지환경부 (mcee.go.kr) | 보도자료 내용을 수집하여 워드클라우드 이미지 생성에 사용 |
| 월별 전기차 등록대수 | 한국스마트그리드협회 charge info | 전기차 등록대수와 뉴스 수의 관계 분석에 사용 |
| 전기차 정책 뉴스 | 네이버 뉴스 | 월별 전기차 보조금 뉴스 수를 수집하여 관계 분석에 사용 |
| FAQ | 기아 · 한국전력 kepco · 현대자동차 · 테슬라 공식 블로그 | FAQ 내용을 수집하여 통합 FAQ 표시에 사용 |

<br>

---
## 📋 ERD 다이어그램
<img width="441" height="535" alt="ERD_DIAGRAM" src="https://github.com/user-attachments/assets/bc684faa-42f7-4bc0-82cd-7eb6757af113" />


<br>

### 🔘 테이블 관계
```
car_registration_stats  1 : N  code_vhcty_asort  (차종코드)
car_registration_stats  1 : N  code_sexdstn      (성별코드)
car_registration_stats  1 : N  code_agrde        (연령대코드)
 
faq             → 독립 테이블
ev_news_monthly → 독립 테이블 (Python에서 year/month 기준 병합)
```

<br>

---
## 📂 프로젝트 구조
```
project/
│
├── db/
│   ├── car_db_faq.sql          # FAQ 관련 테이블 생성 및 데이터 삽입
│   └── ev_register.sql         # car_registration_stats, ev_news_monthly,
│                               # code_vhcty_asort, code_sexdstn, code_agrde 테이블 생성
│
├── faq/
│   ├── faq_cleaner.py          # DB에서 정제 안 된 텍스트 가져와서 브랜드별 정제 후 DB 저장
│   └── faq_crawler.py          # KIA, KEPCO, HYUNDAI, TESLA 크롤링 후 DB 저장
│
├── utils/
│   ├── api_fetch.py            # 공공데이터 API 사용해 DB에 저장
│   └── db_connection.py        # MySQL 연결 객체 반환 (.env 파일에서 설정값 읽어옴)
│
├── views/
│   ├── page1_ev_news_visualize.py  # 정책 뉴스 · 전기차 등록 대수 그래프 시각화
│   ├── page2_subsidy_status.py     # 기후에너지환경부 게시판 iframe으로 시각화
│   ├── page3_buyer_profile.py      # 전기차 구매자 프로파일 시각화
│   ├── page4_faq.py                # FAQ 시각화
│   └── page5_word_cloud.py         # 워드클라우드 시각화
│
├── wordcloud/
│   ├── mcee_crawler.py         # mcee.go.kr 크롤링하여 보도 내용을 엑셀 저장
│   ├── naver_news_crawler.py   # 네이버 뉴스 URL 크롤링하여 DB에 저장
│   ├── result.xlsx             # mcee_crawler.py 결과
│   ├── word_cloud.py           # 엑셀 파일 로드하여 워드클라우드.png 생성
│   └── wordcloud.png           # word_cloud.py 결과
│
├── app.py                      # Streamlit 메인 앱
├── .env                        # DB 환경변수 (Git 업로드 금지)
├── .gitignore
├── requirements.txt
└── README.md
```
 
---
## 🔸 실행 방법

### 1. 레포지토리 클론
```bash
git clone https://github.com/https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN29-1st-3team.git
cd skn_1st_3team
```
 
### 2. 환경변수 설정
`.env` 파일을 생성하고 아래 내용을 입력하세요.
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=ev_dashboard
DB_PORT=3306
PUBLIC_SERVICE_KEY=공공데이터 API KEY
```

### 3. 테이블 생성
```bash
mysql -u root -p < db/ev_register.sql
mysql -u root -p < db/car_db_faq.sql
```

### 4. 크롤링 후 DB 저장
```bash
python utils/api_fetch.py
python utils/naver_news_cralwer.py
python faq/faq_crawler.py
python wordcloud/mcee_crawler.py
python wordcloud/word_cloud.py
```
 
 
### 5. 패키지 설치
```bash
pip install -r requirements.txt
```
 
### 6. Streamlit 실행
```bash
streamlit run app.py
```

<br>

---
## 🖥️ 프로젝트 시연
- **월별 차종별 누적 막대 + 뉴스량 꺾은선 이중축 그래프**
  <img width="1440" height="812" alt="스크린샷 2026-03-30 오후 4 36 43" src="https://github.com/user-attachments/assets/b2cd2dcd-287a-4736-b48b-c65b86ae7961" />

<br>

- **기후에너지환경부 전기차 보조금 관련 보도자료 목록**
  <img width="1440" height="813" alt="스크린샷 2026-03-30 오후 4 40 45" src="https://github.com/user-attachments/assets/f7b1df80-1c4c-4800-b181-5949462c69e0" />

<br>

- **성별 · 연령대 · 차종별 교차분석 차트**
  <img width="1440" height="812" alt="스크린샷 2026-03-30 오후 4 42 18" src="https://github.com/user-attachments/assets/a4fdd027-17ad-47ff-b709-3cf487711ab6" />
  <img width="1440" height="812" alt="스크린샷 2026-03-30 오후 4 42 42" src="https://github.com/user-attachments/assets/078fcb7f-2d74-4215-a8e1-061ff1fea06c" />
  <img width="1440" height="812" alt="스크린샷 2026-03-30 오후 4 42 53" src="https://github.com/user-attachments/assets/98777a53-348c-440b-96a9-135d4cb88fdd" />

<br>

- **FAQ: 브랜드별 전기차 FAQ 통합 검색**
  <img width="1440" height="594" alt="스크린샷 2026-03-30 오후 4 47 29" src="https://github.com/user-attachments/assets/ce87522c-af72-4052-8826-1f76947d91c4" />
  <br>
  
  <img width="1440" height="812" alt="스크린샷 2026-03-30 오후 4 48 28" src="https://github.com/user-attachments/assets/98236489-bc95-41e3-a9e4-52a74aaea719" />
  <br>
  
  <img width="1440" height="813" alt="스크린샷 2026-03-30 오후 4 50 24" src="https://github.com/user-attachments/assets/6a693fd0-108f-487f-a5cd-2c4cb5b1c20b" />
  <br>
  
  <img width="1440" height="812" alt="스크린샷 2026-03-30 오후 4 50 38" src="https://github.com/user-attachments/assets/1eb19580-41cb-48a0-9725-10c9e99cd02b" />

<br>
- **워드클라우드: 정책 보도자료 키워드 빈도 시각화**
  <img width="1440" height="813" alt="스크린샷 2026-03-30 오후 4 54 36" src="https://github.com/user-attachments/assets/c32ce0f1-075f-43f2-a4ae-18c096b49932" />

<br>

---
## ✨ 확장 가능성
- 뉴스 감성 분석(NLP)을 통해 정책의 긍정/부정 영향까지 분석 가능
- 자동 크롤링 파이프라인 구축을 통한 실시간 데이터 업데이트
- 유가, 금리, 충전 인프라 등 외부 변수 결합 분석 가능
- 머신러닝 기반 전기차 수요 예측 모델로 확장 가능

## 🌟 기대 효과
- 정책 변화가 실제 시장에 미치는 영향에 대한 인사이트 제공
- 전기차 구매 트렌드 분석을 통한 정책 설계 지원
- 데이터 기반 의사결정을 위한 시각화 플랫폼 제공

<br>

---
## 회고
### 🙆🏻‍♂️ 박준희
네이버 뉴스 데이터를 수집하는 과정에서 여러 어려움을 겪었습니다. API를 활용하려 했지만 날짜 설정이 불가능해 과거 데이터를 조회할 수 없었고, 결국 크롤링 방식으로 전환해야 했습니다. 또한 네이버 뉴스는 인피니티 스크롤 구조로 되어 있어 데이터를 모두 불러오기까지 반복적인 스크롤이 필요했고, HTML 구조도 복잡해 원하는 정보를 추출하는 데 어려움이 있었습니다. 이 과정을 통해 이론으로 배우는 것과 실제 데이터를 다루는 것은 큰 차이가 있다는 점을 체감할 수 있었습니다.

### 🙆🏻 성주연
API를 활용해 데이터를 수집하는 과정에서 요청 횟수 제한으로 인해 일일 토큰 초과 오류가 발생했다. 수업 때 배운 try-except 문을 활용해 예외 처리를 반복적으로 적용하면서 문제의 원인을 파악할 수 있었다. 또한 DB 테이블을 설계하면서 어떤 테이블을 만들어야 할지 막막했지만, 각 데이터 간의 관계를 고민하고 참조 구조를 직접 그려보며 점차 구조를 구체화할 수 있었다. 이 과정을 통해 데이터 흐름을 설계하는 능력의 중요성을 느꼈다.

### 🙆🏻‍♀️ 임준억
여러 페이지에서 크롤링한 데이터를 하나로 통합하는 과정에서, 데이터 형식이 서로 달라 정제 과정이 가장 큰 어려움으로 느껴졌다. 특히 불필요한 문자나 공백, 구조가 다른 데이터들을 일관되게 맞추는 데이터 정제 과정에서 많은 시행착오를 겪었다. 하지만 강의에서 배운 내용을 바탕으로 크롤링 → DB 적재 → Streamlit 시각화까지 전 과정을 직접 구현해보며, 데이터가 어떻게 흐르고 활용되는지 전체적인 구조를 이해하고 체득할 수 있었다.
