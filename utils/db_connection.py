import os
import pymysql
from dotenv import load_dotenv
 
load_dotenv()
 
def get_connection():
    """MySQL 연결 객체 반환 (.env 파일에서 설정값을 읽어옴)"""
    
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT")),
        charset="utf8mb4",
    )