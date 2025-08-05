"""
Instagram data analyzer
"""

import pandas as pd
from utils.file_utils import load_json_file

def preprocess_instagram_data(file_path, platform_name):
    """인스타그램 분석 데이터 전처리"""
    data = load_json_file(file_path)
    if data is None:
        return None

    all_posts_data = []
    for post in data:
        # 기본적으로 post_summary 구조 사용 (Instagram 공식 계정)
        summary = post.get("post_summary")
        if summary and isinstance(summary, dict):
            post_data = {
                "platform": platform_name,
                "overall_score": summary.get("overall_score"),
                "experience_avg": summary.get("experience_score"),
                "expertise_avg": summary.get("expertise_score"),
                "authoritativeness_avg": summary.get("authoritativeness_score"),
                "trustworthiness_avg": summary.get("trustworthiness_score"),
                "clarity_avg": summary.get("geographic_score", 0),  # geographic_score를 clarity로 사용
                "structure_avg": summary.get("geographic_score", 0),  # 동일값 사용
                "context_avg": summary.get("geographic_score", 0),   # 동일값 사용
                "alignment_avg": summary.get("geographic_score", 0), # 동일값 사용
                "timeliness_avg": summary.get("geographic_score", 0), # 동일값 사용
                "originality_avg": summary.get("geographic_score", 0), # 동일값 사용
                "synergy_avg": (summary.get("overall_score", 0) + summary.get("geographic_score", 0)) / 2,  # 시너지 계산
            }
            all_posts_data.append(post_data)
        
        # UGC 데이터의 경우 ugc_analysis 구조 사용
        ugc = post.get("ugc_analysis")
        if ugc and isinstance(ugc, dict):
            post_data = {
                "platform": platform_name,
                "overall_score": ugc.get("overall_score"),
                "experience_avg": ugc.get("tpo_score", 0),  # TPO를 experience로 사용
                "expertise_avg": ugc.get("styling_score", 0),  # styling을 expertise로 사용
                "authoritativeness_avg": ugc.get("brand_relevance", 0),  # brand_relevance를 authoritativeness로 사용
                "trustworthiness_avg": ugc.get("sentiment_score", 0),  # sentiment를 trustworthiness로 사용
                "clarity_avg": ugc.get("visual_appeal", 0),
                "structure_avg": ugc.get("styling_score", 0),
                "context_avg": ugc.get("tpo_score", 0),
                "alignment_avg": ugc.get("brand_relevance", 0),
                "timeliness_avg": ugc.get("sentiment_score", 0),
                "originality_avg": ugc.get("visual_appeal", 0),
                "synergy_avg": ugc.get("synergy_score", 0),
            }
            all_posts_data.append(post_data)

    if not all_posts_data:
        print(f"{file_path} 파일에서 유효한 데이터를 찾지 못했습니다.")
        return None

    df = pd.DataFrame(all_posts_data)
    score_keys = [k for k in df.columns if k != 'platform']
    for key in score_keys:
        df[key] = pd.to_numeric(df[key], errors='coerce')
        
    return df
