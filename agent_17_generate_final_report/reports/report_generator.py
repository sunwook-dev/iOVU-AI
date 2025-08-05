"""
Main report generation logic
"""

import json
from urllib.parse import quote
from utils.markdown_utils import (
    md_heading, md_image_with_fallback, md_horizontal_rule, 
    md_blockquote, md_centered_image_with_caption
)
from .llm_generator import generate_text_with_llm

def create_comprehensive_report(config, all_data):
    """종합 보고서 생성"""
    parts = []
    brand_name = config["brand_name"]
    # output_folder = config["output_folder"]
    # image_folder = config["image_folder"]
    
    # 실제 차트 저장 경로 (output 폴더 내에 저장)
    chart_path_prefix = config["output_folder"]  # 실제 저장 경로
    # 보고서에서 참조하는 이미지 경로 (markdown 내 참조용)
    input_image_path_prefix = "data/images"  # 보고서 참조 경로
    
    # 제목 섹션
    parts.append(md_heading(f"🏢 KIJUN 브랜드 디지털 채널 최적화 보고서", 1))
    parts.append(f"**작성일**: {config['report_date']}\n**수신**: {config['recipient']}")
    parts.append(md_horizontal_rule())

    # I. 보고서 요약
    parts.append(md_heading("📜 I. 보고서 요약 (Executive Summary)", 2))
    summary_prompt = f"아래 분석 데이터를 종합하여 '{brand_name}' 브랜드의 디지털 채널 현황에 대한 '주요 분석 결과'와 '핵심 권장 전략'을 요약해 주세요. 웹사이트 SEO/GEO 문제점과 소셜미디어 최적화 방안을 중심으로 15줄 이상 작성해 주세요."
    summary_context = json.dumps({
        "platform_performance": "Instagram > Naver Blog > Tistory 순 성과",
        "website_issues": "SEO/GEO 점수 낮음, 메타데이터 부재",
        "ugc_potential": "UGC 활용도 높음, 시너지 편차 존재"
    }, ensure_ascii=False, indent=2)
    summary_text = generate_text_with_llm(summary_prompt, summary_context)
    parts.append(md_blockquote(summary_text))
    parts.append(md_horizontal_rule())

    # II. 공식 웹사이트 분석
    parts.append(md_heading("🌐 II. 공식 웹사이트 분석 및 개선안", 2))
    
    parts.append(md_heading("**II-1. SEO(검색엔진 최적화) 분석**", 3))
    website_seo_prompt = f"웹사이트 SEO 분석 결과를 바탕으로 현황 진단과 개선 전략을 제시해주세요. 메타 설명 부재, 이미지 ALT 속성 부재 등 핵심 문제점을 명시하고 개선 방안을 구체적으로 제안해주세요."
    website_seo_context = json.dumps(all_data.get("website_analysis", {}).get("site_analysis", {}).get("seo", {}), ensure_ascii=False, indent=2)
    parts.append(generate_text_with_llm(website_seo_prompt, website_seo_context))
    parts.append(md_centered_image_with_caption("웹사이트 최적화 전후 비교", f"{chart_path_prefix}/{brand_name}_website_optimization_chart.png", f"{input_image_path_prefix}/{brand_name}_website_optimization_chart.png",500, "웹사이트 최적화 전후 비교"))
    
    parts.append("\n" + md_heading("**II-2. GEO(생성형 엔진 최적화) 분석**", 3))
    website_geo_prompt = f"웹사이트 GEO 분석 데이터를 해석하고, {brand_name} 웹사이트가 생성형 AI 검색 결과에 더 잘 노출되기 위한 대응 전략을 제시해주세요. GEO 6가지 평가 항목별로 현재 점수를 진단하고 개선 방안을 제안해주세요."
    website_geo_context = json.dumps(all_data.get("website_analysis", {}).get("metadata", {}), ensure_ascii=False, indent=2)
    parts.append(generate_text_with_llm(website_geo_prompt, website_geo_context))
    parts.append(md_centered_image_with_caption("웹사이트 GEO 분석", f"{chart_path_prefix}/{brand_name}_website_geo_radar_chart.png", f"{input_image_path_prefix}/{brand_name}_website_geo_radar_chart.png", 400, "웹사이트 GEO 분석 레이더 차트"))
    
    parts.append("\n" + md_heading("**II-3. 로컬 SEO 진단 (지도 서비스 최적화)**", 3))
    map_prompt = f"'{brand_name} {config.get('brand_location', '')}' 의 로컬 SEO 강화를 위한 지도 서비스 최적화 컨설팅 내용을 작성해줘. Google Maps와 Bing Maps 각각에 대해, 사용자가 직접 검색 결과를 확인할 수 있는 링크를 먼저 제공하고, '브랜드가 등록되지 않은 경우'를 위한 신규 등록 가이드와 '이미 등록된 경우'를 위한 프로필 최적화 가이드를 모두 상세히 안내해줘."
    query = f"{brand_name} {config.get('brand_location', '')}"
    map_context = json.dumps({
        "google_search_url": f"https://www.google.com/maps/search/?api=1&query={quote(query)}",
        "bing_search_url": f"https://www.bing.com/maps?q={quote(query)}",
        "google_register_url": "https://www.google.com/business/",
        "bing_register_url": "https://www.bingplaces.com/",
    }, ensure_ascii=False, indent=2)
    parts.append(generate_text_with_llm(map_prompt, map_context))
    
    parts.append(md_horizontal_rule())

    # III. 채널별 종합 분석
    parts.append(md_heading("📊 III. 채널별 종합 분석 (Overall Channel Analysis)", 2))
    
    channel_prompt = """
4개 채널(Instagram 공식, Instagram UGC, Naver Blog, Tistory) 분석 결과를 바탕으로:
1. 아래 표 형식으로 각 채널의 주요 강점과 약점을 요약해주세요.
2. 표 아래에 'UGC 활용 전략' 소제목으로 UGC 활용 방안을 서술해주세요.

| 채널 구분 | 주요 강점 | 주요 약점 |
| :--- | :--- | :--- |
| **Instagram (공식)** | (내용 입력) | (내용 입력) |
| **Instagram (UGC)** | (내용 입력) | (내용 입력) |
| **Naver Blog** | (내용 입력) | (내용 입력) |
| **Tistory** | (내용 입력) | (내용 입력) |
"""
    channel_context = "Instagram 공식 계정 점수가 가장 높고, UGC는 시너지 편차가 큼. Naver/Tistory 블로그는 중간 수준."
    parts.append(generate_text_with_llm(channel_prompt, channel_context))
    
    # 플랫폼 비교 차트 2열 배치
    platform_score_path = f"{chart_path_prefix}/{brand_name}_platform_score_chart.png"
    platform_synergy_path = f"{chart_path_prefix}/{brand_name}_platform_synergy_chart.png"
    
    image_table = f"""
| {md_image_with_fallback("플랫폼별 종합 점수", platform_score_path, f"{input_image_path_prefix}/{brand_name}_platform_score_chart.png", width=400)} | {md_image_with_fallback("플랫폼별 시너지 점수", platform_synergy_path, f"{input_image_path_prefix}/{brand_name}_platform_synergy_chart.png", width=500)} |
| :---: | :---: |
| *플랫폼별 종합 점수* | *플랫폼별 시너지 점수* |
"""
    parts.append(image_table)
    parts.append(md_horizontal_rule())

    # IV. 소셜 채널 (Instagram) 분석
    parts.append(md_heading("📱 IV. 소셜 채널 (Instagram) 심층 분석 및 컨설팅", 2))
    parts.append(md_heading("**IV-1. 콘텐츠 및 UGC 분석**", 3))
    
    insta_analysis_prompt = "인스타그램 공식 계정과 UGC의 분석 데이터를 바탕으로 차이점을 분석하고, 콘텐츠 전략 개선 방안을 제시해주세요."
    insta_analysis_context = json.dumps({"instagram_performance": "공식 계정 우수, UGC 시너지 편차 존재"}, ensure_ascii=False, indent=2)
    parts.append(generate_text_with_llm(insta_analysis_prompt, insta_analysis_context))
    
    # Instagram 차트들
    parts.append(md_centered_image_with_caption("인스타그램 E-E-A-T 분석", f"{chart_path_prefix}/{brand_name}_insta_eeat_line_chart.png", f"{input_image_path_prefix}/{brand_name}_insta_eeat_line_chart.png", 600, "인스타그램 E-E-A-T 분석"))
    parts.append(md_centered_image_with_caption("인스타그램 GEO 분석", f"{chart_path_prefix}/{brand_name}_insta_geo_radar_chart.png", f"{input_image_path_prefix}/{brand_name}_insta_geo_radar_chart.png", 500, "인스타그램 GEO 분석 레이더 차트"))
    
    # Instagram 목업 이미지들
    parts.append(md_heading("**IV-2. 콘텐츠 최적화 예시**", 3))
    parts.append("다음은 분석 결과를 바탕으로 생성된 최적화된 Instagram 콘텐츠 예시입니다:")
    
    # 목업 이미지는 실제 저장 경로(chart_path_prefix)에 저장되지만, 보고서에서는 참조 경로(input_image_path_prefix)를 사용
    insta_official_path = f"{chart_path_prefix}/{config['original_image_files']['insta_official_mockup']}"
    insta_ugc_path = f"{chart_path_prefix}/{config['original_image_files']['insta_ugc_mockup']}"
    
    insta_mockup_table = f"""
| {md_image_with_fallback("공식 계정 최적화 예시", insta_official_path, f"{input_image_path_prefix}/{config['original_image_files']['insta_official_mockup']}", width=300)} | {md_image_with_fallback("UGC 스타일 최적화 예시", insta_ugc_path, f"{input_image_path_prefix}/{config['original_image_files']['insta_ugc_mockup']}", width=300)} |
| :---: | :---: |
| *공식 계정 최적화 예시* | *UGC 스타일 최적화 예시* |
"""
    parts.append(insta_mockup_table)
    parts.append(md_horizontal_rule())

    # V. 블로그 채널 분석
    parts.append(md_heading("📝 V. 블로그 채널 (Naver/Tistory) 분석 및 컨설팅", 2))
    
    blog_analysis_prompt = "Naver 블로그와 Tistory 분석 결과를 바탕으로 각 플랫폼의 특성과 개선 방안을 제시해주세요. 블로그 SEO와 콘텐츠 전략을 중심으로 설명해주세요."
    blog_analysis_context = json.dumps({"blog_performance": "Naver > Tistory, 콘텐츠 최적화 필요"}, ensure_ascii=False, indent=2)
    parts.append(generate_text_with_llm(blog_analysis_prompt, blog_analysis_context))
    
    # 블로그 차트들
    parts.append(md_centered_image_with_caption("블로그 E-E-A-T 분석", f"{chart_path_prefix}/{brand_name}_blog_eeat_line_chart.png", f"{input_image_path_prefix}/{brand_name}_blog_eeat_line_chart.png", 600, "블로그 E-E-A-T 분석"))
    parts.append(md_centered_image_with_caption("블로그 GEO 분석", f"{chart_path_prefix}/{brand_name}_blog_geo_radar_chart.png", f"{input_image_path_prefix}/{brand_name}_blog_geo_radar_chart.png", 500, "블로그 GEO 분석 레이더 차트"))

    # 블로그 컨설팅 이미지
    parts.append(md_centered_image_with_caption("블로그 포스트 컨설팅 예시", f"{chart_path_prefix}/{config['original_image_files']['blog_consulting']}", f"{input_image_path_prefix}/{config['original_image_files']['blog_consulting']}", 600, "블로그 포스트 최적화 컨설팅 예시"))
    parts.append(md_horizontal_rule())

    # VI. 종합 권장사항
    parts.append(md_heading("🎯 VI. 종합 권장사항 및 실행 계획", 2))
    
    recommendation_prompt = f"{brand_name} 브랜드의 디지털 채널 최적화를 위한 종합 권장사항과 단계별 실행 계획을 제시해주세요. 우선순위별로 구체적인 액션 아이템을 나열해주세요."
    recommendation_context = "전체 분석 결과 종합"
    parts.append(generate_text_with_llm(recommendation_prompt, recommendation_context))

    return "\n\n".join(parts)
