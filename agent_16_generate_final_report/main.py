"""
KIJUN 브랜드 디지털 채널 최적화 보고서 - 메인 실행 파일
모듈화된 구조로 재구성된 통합 보고서 생성기

Features:
- Instagram/Blog 데이터 분석 및 차트 생성
- 웹사이트 SEO/GEO 분석 및 차트 생성  
- LLM 기반 보고서 섹션 자동 생성
- 목업 이미지 자동 삽입
"""

#  chart path 수정, 이름
#  보고서 DB저장후 보고서안 image path 수정

import os
import pandas as pd
import dotenv
import mysql.connector
from mysql.connector import Error

# 환경 변수 로드
dotenv.load_dotenv()

# 모듈 임포트
from utils import CONFIG, setup_matplotlib_fonts
from utils.file_utils import load_all_data, save_markdown_file
from analyzers import preprocess_instagram_data, preprocess_blog_data, extract_website_data
from charts import create_platform_comparison_charts, create_website_charts, create_individual_charts
from reports import create_comprehensive_report

def save_report_to_db(file_path):
    """
    Save the generated report to the database.
    """
    
    db_config = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }

    connection = None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            report_content = f.read()

        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            cursor = connection.cursor()
            sql = "INSERT INTO reports (user_id, report_title, report_content, created_at) VALUES (2, 'KIJUN 브랜드 디지털 채널 최적화 심층 분석 및 컨설팅 보고서', %s, NOW())"
            cursor.execute(sql, (report_content,))
            connection.commit()
            print("보고서가 데이터베이스에 성공적으로 저장되었습니다.")
    except FileNotFoundError:
        print(f"오류: 파일을 찾을 수 없습니다. 경로를 확인하세요: {file_path}")
    except Error as e:
        print(f"데이터베이스 오류가 발생했습니다: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("데이터베이스 연결이 닫혔습니다.")

def main():
    """메인 실행 함수"""
    print("🚀 KIJUN 통합 보고서 생성기 시작 (모듈화 버전)")
    print("=" * 60)
    
    # 폰트 설정
    setup_matplotlib_fonts()
    
    # 차트 저장 경로 수정
    CONFIG["output_folder"] = "D:\\AI_src\\FINAL_PROJECT\\iOVU-FRONT\\public\\data\\images"

    # 출력 폴더 생성
    os.makedirs(CONFIG["output_folder"], exist_ok=True)
    
    # 1. 모든 데이터 로드
    print("\n📂 데이터 로드 중...")
    all_data = load_all_data(CONFIG)
    
    # 2. 데이터 전처리
    print("\n🔄 데이터 전처리 중...")
    input_folder = CONFIG["input_folder"]
    
    # Instagram 데이터
    df_insta_official = preprocess_instagram_data(
        os.path.join(input_folder, CONFIG["data_files"]["insta_official_analysis"]), 
        "Instagram (공식)"
    )
    df_insta_ugc = preprocess_instagram_data(
        os.path.join(input_folder, CONFIG["data_files"]["insta_ugc_analysis"]), 
        "Instagram (UGC)"
    )
    
    # 블로그 데이터
    df_naver = preprocess_blog_data(
        os.path.join(input_folder, CONFIG["data_files"]["naver_blog_analysis"]), 
        "Naver Blog"
    )
    df_tistory = preprocess_blog_data(
        os.path.join(input_folder, CONFIG["data_files"]["tistory_blog_analysis"]), 
        "Tistory"
    )
    
    # 웹사이트 데이터
    df_website = extract_website_data(
        os.path.join(input_folder, CONFIG["data_files"]["website_analysis"])
    )
    
    # 데이터 통합
    insta_dfs = [df for df in [df_insta_official, df_insta_ugc] if df is not None and not df.empty]
    blog_dfs = [df for df in [df_naver, df_tistory] if df is not None and not df.empty]
    
    df_insta = pd.concat(insta_dfs, ignore_index=True) if insta_dfs else pd.DataFrame()
    df_blog = pd.concat(blog_dfs, ignore_index=True) if blog_dfs else pd.DataFrame()
    
    # 전체 통합
    all_dfs = [df for df in [df_insta, df_blog] if not df.empty]
    if not all_dfs:
        print("❌ 유효한 데이터가 없습니다.")
        return
    
    df_all = pd.concat(all_dfs, ignore_index=True)
    df_all.fillna(0, inplace=True)
    
    print(f"✅ 통합 데이터: {len(df_all)}개 레코드, {len(df_all['platform'].unique())}개 플랫폼")
    
    # 3. 차트 생성
    print("\n📊 차트 생성 중...")
    brand_name = os.getenv("BRAND_NAME", "BRAND")

    create_platform_comparison_charts(df_all, CONFIG["output_folder"], brand_name)
    create_website_charts(df_website, CONFIG["output_folder"], brand_name)
    create_individual_charts(df_insta, df_blog, CONFIG["output_folder"], brand_name)
    
    # 4. 보고서 생성
    print("\n📝 보고서 생성 중...")
    report_content = create_comprehensive_report(CONFIG, all_data)
    
    # 5. 보고서 저장
    output_path = os.path.join(CONFIG["output_folder"], CONFIG["output_filename"])
    if save_markdown_file(report_content, output_path):
        print(f"\n🎉 보고서 생성 완료!")
        print(f"📄 파일 위치: {output_path}")

        save_report_to_db(output_path)

        # 이미지 파일 존재 여부 확인 메시지
        print("\n📷 이미지 파일 확인:")
        print(f"   차트 이미지: {CONFIG['output_folder']}/ 폴더")
    else:
        print("❌ 보고서 저장 실패")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
