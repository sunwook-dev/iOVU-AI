"""
Configuration settings for the report generator
"""

from datetime import datetime

CONFIG = {
    "brand_name": "KIJUN",
    "brand_location": "서울시 용산구 이태원로54길 19",
    "report_date": datetime.now().strftime("%Y년 %m월 %d일"),
    "recipient": "KIJUN 마케팅팀",
    "output_filename": "KIJUN_브랜드_디지털채널_최적화_보고서_통합본.md",
    "llm_model": "gpt-4o-mini",
    "input_folder": "./input",
    "image_folder": "./input/image",
    "output_folder": "./output",
    "data_files": {
        "website_analysis": "multipage_detailed_data_20250722_121539.json",
        "insta_official_analysis": "kijun_official_eeatg_analysis.json",
        "insta_official_generated": "kijun_official_generated_content.json",
        "insta_ugc_analysis": "kijun_official_tagged_ugc_combined_analysis.json",
        "insta_ugc_generated": "kijun_official_tagged_ugc_generated_content.json",
        "naver_blog_analysis": "naver_analysis_report.json",
        "tistory_blog_analysis": "tistory_analysis_report.json",
        "naver_blog_consulting": "naver_consulting_report.json",
        "tistory_blog_consulting": "tistory_consulting_report.json",
    },
    "original_image_files": {
        "insta_official_mockup": "kijun_official_instagram_mockup.jpg",
        "insta_ugc_mockup": "kijun_official_tagged_ugc_instagram_mockup.jpg", 
        "blog_consulting": "kijun_blog_post_consulting_id_3.png",
    }
}
