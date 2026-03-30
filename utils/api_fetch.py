import requests
import xml.etree.ElementTree as ET
import os
import sys
import time
from datetime import date

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from utils.db_connection import get_connection

load_dotenv()

# 환경 변수 및 설정
SERVICE_KEY  = os.getenv("PUBLIC_SERVICE_KEY")
URL          = "https://apis.data.go.kr/B553881/newRegistlnfoService_02/getnewRegistlnfoService02"
FUEL_CODE    = "5"            # 전기차
VHCTY_CODES  = ["1", "2", "3", "4"] # 승용/승합/화물/특수
SEXDSTN_CODE = {"남자": 1, "여자": 2, "법인": 0}
AGRDE_LIST   = ["1", "2", "3", "4", "5", "6", "7", "8"] # 10대~80대

# 수집 범위
# 2017년 1월 - 2026년 2월까지 저장됨 
START_YEAR, START_MONTH = 2017, 1
END_YEAR, END_MONTH = 2026, 2

def call_api(params):
    """API 호출 후 (resultCode, dtaCo) 반환"""
    try:
        response = requests.get(URL, params=params, timeout=10)
        if response.status_code != 200:
            return None, 0
        
        root = ET.fromstring(response.text)
        result_code = root.findtext("header/resultCode")
        dta_co = int(root.findtext("body/dtaCo") or 0)
        return result_code, dta_co
    
    except Exception as e:
        print(f" call_api 오류: {e}")
        return None, 0

def save_rows(rows):
    """리스트를 DB에 저장"""
    if not rows:
        return
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO car_registration_stats
                    (regist_yy, regist_mt, vhcty_asort_code,
                      sexdstn, agrde, cnt)
                VALUES
                    (%(regist_yy)s, %(regist_mt)s, %(vhcty_asort_code)s,
                     %(sexdstn)s, %(agrde)s, %(cnt)s)
            """
            cur.executemany(sql, rows)
        conn.commit()
    except Exception as e:
        print(f" DB 저장 오류: {e}")
        conn.rollback()
    finally:
        conn.close()

def run():
    """등록연월 × 차종 × 성별 × 연령대 조합으로 API 호출 후 저장"""
    total_saved = 0

    year, month = START_YEAR, START_MONTH
    while (year, month) <= (END_YEAR, END_MONTH):
        month_rows = []
        
        for vhcty in VHCTY_CODES:
            for sexdstn in SEXDSTN_CODE.keys():
                # 법인은 연령대 "0", 개인은 "1"~"8"
                agrde_targets = ["0"] if sexdstn == "법인" else AGRDE_LIST
                
                for agrde in agrde_targets:
                    params = {
                        "serviceKey": SERVICE_KEY,
                        "registYy": str(year),
                        "registMt": f"{month:02d}",
                        "vhctyAsortCode": vhcty,
                        "sexdstn": sexdstn,
                        "agrde": agrde,
                        "useFuelCode": FUEL_CODE
                    }
                    
                    code, cnt = call_api(params)
                    
                    # 정상 응답이고 등록 건수가 있을 때만 저장
                    if code == "00" and cnt > 0:
                        month_rows.append({
                            "regist_yy":        int(year),
                            "regist_mt":        int(month),
                            "vhcty_asort_code": int(vhcty),
                            "sexdstn":          SEXDSTN_CODE[sexdstn],  # "남자" → 1
                            "agrde":            int(agrde),
                            "cnt":              cnt
                        })
                    
                    time.sleep(0.2)

        save_rows(month_rows)
        total_saved += len(month_rows)
        print(f"  {year}-{month:02d}  {len(month_rows)}건 저장")

        # 다음 달로 이동
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    print(f"api_fetch run() 완료: 총 {total_saved}개 저장")

if __name__ == "__main__":
    run()