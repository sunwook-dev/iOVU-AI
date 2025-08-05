#!/usr/bin/env python3
"""유니폼 브릿지 브랜드 등록"""
import pymysql
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# DB 연결
conn = pymysql.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'modular_agents_db'),
    charset='utf8mb4'
)

try:
    cursor = conn.cursor()
    
    # 브랜드 등록
    insert_brand = """
    INSERT INTO brands (
        brand_official_name,
        hq_country,
        price_positioning
    ) VALUES (%s, %s, %s)
    """
    cursor.execute(insert_brand, ("Uniform Bridge", "KR", "Mid-tier"))
    brand_id = cursor.lastrowid
    
    # 브랜드 채널 등록
    insert_channels = """
    INSERT INTO brand_channels (
        brand_id,
        official_site_url,
        instagram_handle
    ) VALUES (%s, %s, %s)
    """
    cursor.execute(insert_channels, (brand_id, "https://uniformbridge.com", "uniformbridge"))
    
    conn.commit()
    print(f"✅ 브랜드 등록 완료!")
    print(f"   - Brand ID: {brand_id}")
    print(f"   - Brand Name: Uniform Bridge")
    print(f"   - Homepage: https://uniformbridge.com")
    print(f"   - Instagram: @uniformbridge")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()