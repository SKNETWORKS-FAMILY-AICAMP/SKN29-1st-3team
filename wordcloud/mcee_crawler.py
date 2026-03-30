import requests
from bs4 import BeautifulSoup
import time
from openpyxl import Workbook

# =========================
# 기본 설정
# =========================
BASE_URL = "https://www.mcee.go.kr"  # 도메인
LIST_URL = "https://www.mcee.go.kr/home/web/board/list.do"  # 목록 페이지 API

HEADERS = {
    "User-Agent": "Mozilla/5.0"  # 크롤링 차단 회피용 (기본 헤더)
}


# =========================
# 게시글 목록 가져오기
# =========================
def get_list(page=0):
    # 서버에 전달할 쿼리 파라미터
    params = {
        "maxPageItems": 50,           # 한 페이지당 게시글 수
        "maxIndexPages": 10,
        "searchKey": "titleOrContent",
        "searchValue": "전기차 보조금",  # 검색 키워드
        "boardMasterId": 1,
        "menuId": 10525,
        "pagerOffset": page          # 페이지 offset (0, 50, 100 ...)
    }

    # 목록 페이지 요청
    res = requests.get(LIST_URL, params=params, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    # 게시글 리스트 영역 선택
    rows = soup.select("#content_body table tbody tr")

    data = []

    for row in rows:
        # 제목 + 링크 태그
        a_tag = row.select_one("td.al > a")

        if not a_tag:
            continue  # 광고/빈 row 제거

        # title 속성에 실제 제목이 들어있는 구조
        title = a_tag.get("title", "").strip()

        # 상세 페이지 상대경로
        href = a_tag.get("href", "").strip()

        print(title, href)  # 디버깅용 출력

        data.append({
            "title": title,
            "link": BASE_URL + href  # 절대경로로 변환
        })

    return data


# =========================
# 게시글 상세 내용 가져오기
# =========================
def get_detail(url):
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    # 본문 영역 (사이트 구조 의존적 → 바뀌면 여기 수정 필요)
    content_tag = soup.select_one("#boardTableWrapper > div.view_con")
    
    if content_tag:
        # 줄바꿈 유지하면서 텍스트 추출
        content = content_tag.get_text("\n", strip=True)
    else:
        content = ""  # 본문 없는 경우 대비
        
    return content


# =========================
# 엑셀 저장
# =========================
def save_to_excel(data, filename="result.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.title = "articles"

    # 헤더 (컬럼 구조 정의)
    ws.append(["title", "url", "content"])

    # 데이터 입력
    for d in data:
        ws.append([
            d["title"],
            d["url"],
            d["content"]
        ])

    wb.save(filename)
    print(f"엑셀 저장 완료: {filename}")


# =========================
# 크롤링 메인 로직
# =========================
def crawl(max_pages=5):
    results = []

    # pagerOffset 기준으로 페이지 순회
    # 0, 50, 100 ... 형태로 증가
    for page in range(0, max_pages * 50, 50):
        print(f"페이지 offset: {page}")

        items = get_list(page)

        # 더 이상 데이터 없으면 종료
        if not items:
            break

        for item in items:
            print("수집:", item["title"])

            # 상세 페이지 크롤링
            content = get_detail(item["link"])
            print(content)  # 디버깅용

            results.append({
                "title": item["title"],
                "content": content,
                "url": item["link"]
            })

            # 서버 부하 및 차단 방지
            time.sleep(0.3)

    return results


# =========================
# 실행 진입점
# =========================
if __name__ == "__main__":
    # 크롤링 실행 (페이지 수 조절 가능)
    data = crawl(max_pages=3)

    # 결과 엑셀 저장
    save_to_excel(data)

    # 일부 데이터 확인용 (디버깅)
    # for d in data[:3]:
    #     print("="*50)
    #     print(d["title"])
    #     print(d["content"][:200])