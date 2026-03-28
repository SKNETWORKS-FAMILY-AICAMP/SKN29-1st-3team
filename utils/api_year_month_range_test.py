'''
공공데이터포털 자동차 신규등록정보 API의 데이터 등록연도, 등록월 범위 찾는 코드

# ===== 결과 =====
# 최초 데이터: (2015, 1)
# 최신 데이터: (2026, 2)
'''

import requests
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv

load_dotenv()

service_key = os.getenv('PUBLIC_SERVICE_KEY')
url = 'https://apis.data.go.kr/B553881/newRegistlnfoService_02/getnewRegistlnfoService02'

start_year = 2015
end_year = 2026

available_data = []

for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        params = {
            'serviceKey': service_key,
            'registYy': str(year),
            'registMt': f'{month:02}',
            'useFuelCode': 5
        }

        response = requests.get(url, params=params)
        root = ET.fromstring(response.text)

        count = root.findtext('body/dtaCo')

        try:
            count_int = int(count)
        except:
            count_int = 0

        if count_int > 0:
            print(f"{year}-{month:02} 있음 ({count_int})")
            available_data.append((year, month))
        else:
            print(f"{year}-{month:02} 없음")

if available_data:
    print("\n===== 결과 =====")
    print("최초 데이터:", min(available_data))
    print("최신 데이터:", max(available_data))
    
