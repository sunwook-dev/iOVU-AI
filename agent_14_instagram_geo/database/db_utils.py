# -*- coding: utf-8 -*-
"""
데이터베이스 유틸리티 - Instagram 데이터 조회 (agent_03_instagram_crawler 연동)
"""

import mysql.connector
from datetime import datetime
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    from database.config import db_config
    USE_SHARED_CONFIG = True
except ImportError:
    USE_SHARED_CONFIG = False
    print("공용 DB 설정을 사용할 수 없어 로컬 설정을 사용합니다.")

load_dotenv()


def get_db_connection():
    """데이터베이스 연결 생성 (공용 설정 우선 사용)"""
    try:
        if USE_SHARED_CONFIG:
            # 공용 DB 설정 사용
            connection = mysql.connector.connect(
                host=db_config.host,
                user=db_config.user,
                password=db_config.password,
                database=db_config.database,
                charset=db_config.charset,
                port=db_config.port
            )
        else:
            # 로컬 환경변수 사용
            connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', '1234'),
                database=os.getenv('DB_NAME', 'modular_agents_db'),
                charset='utf8mb4',
                port=int(os.getenv('DB_PORT', '3306'))
            )
        return connection
    except mysql.connector.Error as e:
        print(f"데이터베이스 연결 실패: {e}")
        return None


def get_brand_id(brand_name="KIJUN"):
    """브랜드 ID 조회"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM 01_brands WHERE brand_official_name = %s", (brand_name,))
        result = cursor.fetchone()
        
        if result:
            print(f"✅ 브랜드 '{brand_name}' ID 찾음: {result[0]}")
            return result[0]
        else:
            print(f"⚠️ 브랜드 '{brand_name}'을 찾을 수 없습니다.")
            return None
            
    except mysql.connector.Error as e:
        print(f"❌ 브랜드 ID 조회 실패: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def is_ugc_post(post_data):
    """UGC 여부 판단 로직"""
    # 1. 계정명으로 구분 (kijun_official이 아닌 경우 UGC)
    raw_data = post_data.get('raw_data', {})
    if isinstance(raw_data, str):
        try:
            raw_data = json.loads(raw_data)
        except:
            raw_data = {}
    
    # href URL에서 계정명 추출
    href = post_data.get('href', '')
    if href and '/p/' in href:
        # URL 패턴: https://www.instagram.com/계정명/p/포스트ID/
        parts = href.split('/')
        if len(parts) >= 4:
            account_name = parts[3]  # 계정명 위치
            if account_name != 'kijun_official':
                return True
    
    # 2. raw_data에서 계정 정보 확인
    if 'owner' in raw_data:
        owner_username = raw_data['owner'].get('username', '')
        if owner_username and owner_username != 'kijun_official':
            return True
    
    # 3. 멘션이나 태그에서 kijun 관련 태그 확인
    mentions = post_data.get('mentions', [])
    if mentions and any('kijun' in str(mention).lower() for mention in mentions):
        return True
    
    # 4. 해시태그에서 kijun 관련 태그 확인 (UGC 가능성)
    hashtags = post_data.get('hashtags', [])
    if hashtags:
        kijun_tags = [tag for tag in hashtags if 'kijun' in str(tag).lower()]
        # 공식 계정이 아니면서 kijun 태그가 있으면 UGC로 판단
        if kijun_tags and not href.find('kijun_official') > 0:
            return True
    
    return False


def get_instagram_data_from_db(brand_name="KIJUN", limit=50, data_type="all"):
    """
    데이터베이스에서 Instagram 데이터 가져오기
    data_type: "all", "official", "ugc"
    """
    print(f"데이터베이스에서 {brand_name} Instagram 데이터 조회 중... (타입: {data_type})")
    
    # 브랜드 ID 조회
    brand_id = get_brand_id(brand_name)
    if not brand_id:
        print(f"브랜드 '{brand_name}'의 데이터를 찾을 수 없습니다.")
        return []
    
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Instagram 데이터 조회
        query = """
        SELECT 
            id,
            post_id,
            shortcode,
            post_type,
            caption,
            hashtags,
            mentions,
            location_info,
            media_urls,
            thumbnail_url,
            likes_count,
            comments_count,
            views_count,
            is_sponsored,
            posted_at,
            raw_data,
            crawled_at
        FROM 03_raw_instagram_data 
        WHERE brand_id = %s 
        ORDER BY posted_at DESC 
        LIMIT %s
        """
        
        cursor.execute(query, (brand_id, limit))
        results = cursor.fetchall()
        
        print(f"{len(results)}개의 Instagram 게시물 데이터를 가져왔습니다.")
        
        # 데이터를 JSON 형태로 변환
        processed_data = []
        for row in results:
            # JSON 필드 파싱
            try:
                if row['hashtags'] and isinstance(row['hashtags'], str):
                    row['hashtags'] = json.loads(row['hashtags'])
                if row['mentions'] and isinstance(row['mentions'], str):
                    row['mentions'] = json.loads(row['mentions'])
                if row['location_info'] and isinstance(row['location_info'], str):
                    row['location_info'] = json.loads(row['location_info'])
                if row['media_urls'] and isinstance(row['media_urls'], str):
                    row['media_urls'] = json.loads(row['media_urls'])
                if row['raw_data'] and isinstance(row['raw_data'], str):
                    row['raw_data'] = json.loads(row['raw_data'])
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류 (post_id: {row['post_id']}): {e}")
            
            # 날짜 처리
            if row['posted_at']:
                row['posted_at'] = row['posted_at'].isoformat() if hasattr(row['posted_at'], 'isoformat') else str(row['posted_at'])
            if row['crawled_at']:
                row['crawled_at'] = row['crawled_at'].isoformat() if hasattr(row['crawled_at'], 'isoformat') else str(row['crawled_at'])
            
            processed_data.append(row)
        
        # 데이터 타입에 따라 필터링
        if data_type == "all":
            return processed_data
        elif data_type == "official":
            return [post for post in processed_data if not is_ugc_post(post)]
        elif data_type == "ugc":
            return [post for post in processed_data if is_ugc_post(post)]
        else:
            return processed_data
        
    except mysql.connector.Error as e:
        print(f"Instagram 데이터 조회 실패: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def convert_db_data_to_json_format(db_data, add_number=True):
    """DB 데이터를 기존 JSON 형태로 변환 (agent_03_crawler와 호환)"""
    json_data = []
    
    for i, post in enumerate(db_data, 1):
        # raw_data에서 href 추출 시도
        raw_data = post.get('raw_data', {})
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except:
                raw_data = {}
        
        # href 생성 (raw_data에서 우선 추출, 없으면 shortcode로 생성)
        href = ""
        if raw_data and 'permalink' in raw_data:
            href = raw_data['permalink']
        elif raw_data and 'href' in raw_data:
            href = raw_data['href']
        elif post.get('shortcode'):
            href = f"https://www.instagram.com/p/{post.get('shortcode')}/"
        
        # 기존 JSON 형태에 맞게 변환 (agent_03 crawler 형식과 동일)
        json_post = {
            "href": href,
            "content": post.get('caption', ''),
            "date": post.get('posted_at', ''),
            "img": post.get('media_urls', []) if post.get('media_urls') else [],
            "comments": [],  # 실제 댓글 데이터가 있다면 여기에 추가
        }
        
        # number 필드 추가 (기존 JSON과 호환)
        if add_number:
            json_post["number"] = i
        
        # 추가 메타데이터 (기존 JSON에는 없었지만 유용한 정보)
        json_post.update({
            "likes_count": post.get('likes_count', 0),
            "comments_count": post.get('comments_count', 0),
            "views_count": post.get('views_count', 0),
            "hashtags": post.get('hashtags', []),
            "mentions": post.get('mentions', []),
            "post_type": post.get('post_type', 'image'),
            "is_sponsored": post.get('is_sponsored', False),
            "db_id": post.get('id'),
            "post_id": post.get('post_id', ''),
            "shortcode": post.get('shortcode', '')
        })
        
        json_data.append(json_post)
    
    return json_data


def save_db_data_to_json(brand_name="KIJUN", output_dir="./"):
    """DB 데이터를 UGC/공식 구분하여 JSON 파일로 저장 (agent_03과 호환)"""
    print(f"{brand_name} Instagram DB 데이터를 JSON으로 저장 중...")
    
    # DB에서 공식 데이터와 UGC 데이터 각각 가져오기
    official_db_data = get_instagram_data_from_db(brand_name, data_type="official")
    ugc_db_data = get_instagram_data_from_db(brand_name, data_type="ugc")
    
    if not official_db_data and not ugc_db_data:
        print("저장할 데이터가 없습니다.")
        return None, None
    
    print(f"공식 데이터: {len(official_db_data)}개, UGC 데이터: {len(ugc_db_data)}개")
    
    saved_files = []
    all_data = []
    
    # 공식 데이터 처리 및 저장 ({brand_name}_official.json 형태)
    if official_db_data:
        official_json_data = convert_db_data_to_json_format(official_db_data)
        official_filename = os.path.join(output_dir, f"{brand_name}_official.json")
        
        with open(official_filename, 'w', encoding='utf-8') as f:
            json.dump(official_json_data, f, ensure_ascii=False, indent=2)
        print(f"공식 데이터 저장: {official_filename} ({len(official_json_data)}개 게시물)")
        saved_files.append(official_filename)
        all_data.extend(official_json_data)
    
    # UGC 데이터 처리 및 저장 ({brand_name}_official_tagged.json 형태)
    if ugc_db_data:
        ugc_json_data = convert_db_data_to_json_format(ugc_db_data)
        ugc_filename = os.path.join(output_dir, f"{brand_name}_official_tagged.json")
        
        with open(ugc_filename, 'w', encoding='utf-8') as f:
            json.dump(ugc_json_data, f, ensure_ascii=False, indent=2)
        print(f"UGC 데이터 저장: {ugc_filename} ({len(ugc_json_data)}개 게시물)")
        saved_files.append(ugc_filename)
        all_data.extend(ugc_json_data)
    
    return saved_files, all_data


def test_db_connection():
    """데이터베이스 연결 테스트"""
    print("DB 연결 테스트 중...")
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # 테이블 존재 확인
        cursor.execute("SHOW TABLES LIKE '03_raw_instagram_data'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("03_raw_instagram_data 테이블 존재")
            
            # 데이터 개수 확인
            cursor.execute("SELECT COUNT(*) FROM 03_raw_instagram_data")
            count = cursor.fetchone()[0]
            print(f"Instagram 데이터 개수: {count}개")
            
            # 브랜드별 데이터 확인
            cursor.execute("""
                SELECT b.brand_name, COUNT(i.id) as post_count
                FROM 01_brands b
                LEFT JOIN 03_raw_instagram_data i ON b.id = i.brand_id
                GROUP BY b.id, b.brand_name
                HAVING post_count > 0
            """)
            brand_data = cursor.fetchall()
            
            print("브랜드별 Instagram 데이터:")
            for brand_name, post_count in brand_data:
                print(f"  - {brand_name}: {post_count}개 게시물")
            
            return True
        else:
            print("03_raw_instagram_data 테이블이 존재하지 않습니다.")
            return False
            
    except mysql.connector.Error as e:
        print(f"데이터베이스 테스트 실패: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

