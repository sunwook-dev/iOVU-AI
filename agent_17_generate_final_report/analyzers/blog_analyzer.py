"""
Blog data analyzer  
"""

import pandas as pd
from utils.file_utils import load_json_file

def preprocess_blog_data(file_path, platform_name):
    """블로그 분석 데이터 전처리 (Naver/Tistory)"""
    data = load_json_file(file_path)
    if data is None:
        return None

    all_posts_data = []
    for item in data:
        report = item.get("analysis_report")
        if not report:
            continue

        summary = report.get("summary", {})
        eeat = report.get("eeat_evaluation", {})
        geo = report.get("geo_analysis", {})
        synergy = report.get("synergy_analysis", {})

        # Synergy 점수 계산
        consistency_score = synergy.get('consistency', {}).get('score')
        synergy_effect_score = synergy.get('synergy_effect', {}).get('score')
        synergy_avg = None
        if consistency_score is not None and synergy_effect_score is not None:
            synergy_avg = (consistency_score + synergy_effect_score) / 2

        post_data = {
            "platform": platform_name,
            "overall_score": summary.get("average_score"),
            "experience_avg": eeat.get("experience", {}).get("score"),
            "expertise_avg": eeat.get("expertise", {}).get("score"),
            "authoritativeness_avg": eeat.get("authoritativeness", {}).get("score"),
            "trustworthiness_avg": eeat.get("trustworthiness", {}).get("score"),
            "clarity_avg": geo.get("clarity_and_specificity", {}).get("score"),
            "structure_avg": geo.get("structured_information", {}).get("score"),
            "context_avg": geo.get("contextual_richness", {}).get("score"),
            "alignment_avg": geo.get("visual_text_alignment", {}).get("score"),
            "timeliness_avg": geo.get("timeliness_and_event_relevance", {}).get("score"),
            "originality_avg": geo.get("originality", {}).get("score"),
            "synergy_avg": synergy_avg,
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
