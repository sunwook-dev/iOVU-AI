"""
Content analysis tools for Instagram posts
"""

import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def analyze_single_file(filename):
    """1단계: 단일 파일 분석"""
    print(f"\n📊 1단계: {filename} 분석 시작")
    
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API 키가 .env 파일에 설정되지 않았습니다.")
        return False
    
    print(f"✅ OpenAI API 키 확인됨: {api_key[:10]}...")
    client = OpenAI(api_key=api_key)
    
    if not os.path.exists(filename):
        print(f"⚠️ {filename} 파일이 존재하지 않습니다.")
        return False
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ 데이터 로드: {len(data)}개 게시물")
        
        # UGC 여부 판단
        is_ugc_dataset = 'tagged' in filename.lower()
        print(f"📋 데이터셋 유형: {'UGC 포함' if is_ugc_dataset else '공식 게시물 전용'}")
        
        detailed_analyses = []
        
        # 모든 게시물 분석 (12개 전체)
        for i, post in enumerate(data, 1):
            print(f"📝 게시물 {i}/{len(data)} 분석 중...")
            
            url = post.get('href', '')
            content = post.get('content', '')
            date = post.get('date', '')
            comments = post.get('comments', [])
            
            print(f"  📍 URL: {url[:50]}...")
            print(f"  🏷️ 타입: {'UGC' if is_ugc_dataset else '공식 게시물'}")
            
            if is_ugc_dataset:
                analysis_prompt = _create_ugc_analysis_prompt(url, content, date, len(comments))
            else:
                analysis_prompt = _create_official_analysis_prompt(url, content, date, len(comments))
            
            try:
                # OpenAI API 호출
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert marketing analyst specializing in Instagram content analysis."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
                
                analysis_text = response.choices[0].message.content
                print(f"  🤖 LLM 분석 완료")
                
                # JSON 파싱 시도
                analysis_json = _parse_analysis_json(analysis_text, i)
                        
            except Exception as e:
                print(f"  ❌ LLM 분석 실패: {e}")
                # API 실패시 기본값 사용
                analysis_json = {
                    "overall_score": 75,
                    "summary": f"게시물 {i} 분석 오류",
                    "overall_suggestion": f"게시물 {i} 개선 필요"
                }
            
            post_analysis = {
                "post_url": url,
                "original_post_data": {
                    "number": i,
                    "href": url,
                    "content": content,
                    "img": post.get('img', []),
                    "comments": comments,
                    "date": date
                },
                "post_summary": analysis_json
            }
            
            # UGC 분석인 경우 추가 필드 저장
            if is_ugc_dataset and 'product_guess' in analysis_json:
                post_analysis['ugc_analysis'] = analysis_json
            
            detailed_analyses.append(post_analysis)
            score = analysis_json.get('overall_score', 75)
            print(f"  ✅ 완료 - 점수: {score}/100점")
        
        # 점수별 정렬
        sorted_analyses = sorted(detailed_analyses, key=lambda x: x['post_summary']['overall_score'])
        
        # 하위 점수 게시물에 대한 개선안 생성
        low_score_posts = sorted_analyses[:2]
        low_score_revisions = []
        
        print(f"\n💡 하위 점수 게시물 개선안 생성 중...")
        
        for post in low_score_posts:
            revision_data = _generate_revision(client, post)
            low_score_revisions.append(revision_data)
        
        # 상위 점수 게시물 성공 요인 분석
        high_score_posts = sorted_analyses[-2:] if len(sorted_analyses) >= 2 else sorted_analyses[-1:]
        high_score_analyses = []
        
        print(f"\n🏆 상위 점수 게시물 성공 요인 분석 중...")
        
        for post in high_score_posts:
            success_data = _analyze_success_factors(client, post)
            high_score_analyses.append(success_data)
        
        # 파일명 결정
        base_name = filename.replace('.json', '')
        
        # UGC 포함 여부 확인
        ugc_count = len([p for p in detailed_analyses if 'ugc_analysis' in p])
        has_ugc = ugc_count > 0
        
        if has_ugc:
            analysis_filename = os.path.join('output', f'{base_name}_ugc_combined_analysis.json')
            content_filename = os.path.join('output', f'{base_name}_ugc_generated_content.json')
            print(f"💡 UGC 포함 분석으로 파일명: {analysis_filename}")
        else:
            analysis_filename = os.path.join('output', f'{base_name}_eeatg_analysis.json')
            content_filename = os.path.join('output', f'{base_name}_generated_content.json')
            print(f"💡 공식 게시물 전용 분석 파일명: {analysis_filename}")
        
        # 상세 분석 결과 저장
        with open(analysis_filename, 'w', encoding='utf-8') as f:
            json.dump(detailed_analyses, f, ensure_ascii=False, indent=4)
        
        # 콘텐츠 파일 저장
        content_suggestions = {
            "low_score_revisions": low_score_revisions,
            "high_score_analyses": high_score_analyses
        }
        
        with open(content_filename, 'w', encoding='utf-8') as f:
            json.dump(content_suggestions, f, ensure_ascii=False, indent=4)
        
        print(f"✅ 1단계 완료 - 파일 저장:")
        print(f"  📊 분석 파일: {analysis_filename}")
        print(f"  💡 콘텐츠 파일: {content_filename}")
        return content_filename
        
    except Exception as e:
        print(f"❌ {filename} 분석 실패: {e}")
        return False


def _create_ugc_analysis_prompt(url, content, date, comments_count):
    """UGC 상세 분석 프롬프트 생성"""
    return f"""
    You are a 'Senior Marketing Strategist' analyzing a KIJUN brand UGC Instagram post.
    Perform a comprehensive 3-step analysis and provide final scoring.
    
    POST DATA:
    URL: {url}
    Caption: {content}
    Date: {date}
    Comments: {comments_count}
    
    STEP 1 - Product & TPO Analysis:
    From the image and caption, identify the KIJUN product and analyze the TPO (Time, Place, Occasion).
    Score how well the product fits the TPO situation (1-100).
    
    STEP 2 - Styling Analysis:
    Define the styling mood, list paired items, and score the styling creativity (1-100).
    Focus on how creatively the KIJUN item is styled with other pieces.
    
    STEP 3 - Sentiment Analysis:
    Analyze the user's emotional expression and satisfaction level (0-100 points).
    Look for positive emotions, satisfaction indicators, and brand affinity.
    
    Provide your analysis in JSON format with detailed Korean explanations:
    {{
        "product_guess": "추정 제품명",
        "tpo_analysis": "TPO 상황 분석",
        "tpo_score": 점수 (0-100),
        "tpo_reason": "TPO 적절성 평가 이유",
        "styling_mood": "스타일링 무드 정의",
        "paired_items": "함께 매치된 아이템들",
        "styling_score": 점수 (0-100),
        "styling_reason": "스타일링 창의성 평가 이유",
        "sentiment_score": 점수 (0-100),
        "sentiment_reason": "감정적 어필 및 만족도 분석",
        "brand_relevance": 점수 (0-100),
        "brand_reason": "브랜드 연관성 및 충성도 분석",
        "visual_appeal": 점수 (0-100),
        "visual_reason": "시각적 매력도 평가",
        "synergy_score": 점수 (0-100),
        "synergy_reason": "이미지와 캡션의 연결성 분석",
        "overall_score": 평균점수 (0-100),
        "summary": "UGC 전체 요약 및 브랜드 가치",
        "overall_suggestion": "UGC 활용 및 브랜드 마케팅 제안"
    }}
    """


def _create_official_analysis_prompt(url, content, date, comments_count):
    """공식 게시물 E-E-A-T-GEO 분석 프롬프트 생성"""
    return f"""
    You are a 'Senior Digital Marketing Analyst' analyzing official KIJUN Instagram content.
    Perform comprehensive E-E-A-T-GEO analysis and provide detailed scoring.
    
    POST DATA:
    URL: {url}
    Caption: {content}
    Date: {date}
    Comments: {comments_count}
    
    ANALYSIS FRAMEWORK (E-E-A-T-GEO):
    - Experience: User experience quality
    - Expertise: Fashion expertise demonstration  
    - Authoritativeness: Brand authority signals
    - Trustworthiness: Content credibility
    - Geographic: Location/cultural relevance
    
    Provide detailed analysis in JSON format with Korean explanations:
    {{
        "experience_score": 점수 (0-100),
        "experience_reason": "사용자 경험 품질 분석",
        "expertise_score": 점수 (0-100),
        "expertise_reason": "패션 전문성 시연 분석",
        "authoritativeness_score": 점수 (0-100),
        "authoritativeness_reason": "브랜드 권위성 신호 분석",
        "trustworthiness_score": 점수 (0-100),
        "trustworthiness_reason": "콘텐츠 신뢰성 분석",
        "geographic_score": 점수 (0-100),
        "geographic_reason": "지리적/문화적 연관성 분석",
        "overall_score": 평균점수 (0-100),
        "summary": "E-E-A-T-GEO 전체 분석 요약",
        "overall_suggestion": "콘텐츠 개선 및 최적화 제안"
    }}
    """


def _parse_analysis_json(analysis_text, post_number):
    """분석 결과 JSON 파싱"""
    try:
        # JSON 부분만 추출 (더 유연한 방법)
        # 중괄호로 둘러싸인 JSON 패턴 찾기
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        json_matches = re.findall(json_pattern, analysis_text, re.DOTALL)
        
        if json_matches:
            # 가장 긴 JSON 문자열 선택
            json_text = max(json_matches, key=len)
            analysis_json = json.loads(json_text)
        else:
            # 직접 JSON 시작/끝 찾기
            json_start = analysis_text.find('{')
            json_end = analysis_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_text = analysis_text[json_start:json_end]
                analysis_json = json.loads(json_text)
            else:
                raise ValueError("JSON 형식을 찾을 수 없습니다.")
                
    except Exception as json_error:
        print(f"  ⚠️ JSON 파싱 실패 ({json_error}) - 기본값 사용")
        # JSON 파싱 실패시 기본값 사용
        analysis_json = {
            "overall_score": 75,
            "summary": f"게시물 {post_number} LLM 분석 완료 (파싱 오류)",
            "overall_suggestion": f"게시물 {post_number} 개선 제안"
        }
    
    return analysis_json


def _generate_revision(client, post):
    """하위 점수 게시물 개선안 생성"""
    print(f"  📝 하위 점수 게시물 개선안 생성 중...")
    
    revision_prompt = f"""
    You are a senior Creative Director for the fashion brand 'KIJUN'.
    An underperforming post needs revision based on comprehensive analysis.
    
    ORIGINAL POST DATA:
    URL: {post['post_url']}
    Original Caption: {post['original_post_data']['content']}
    Current Score: {post['post_summary']['overall_score']}
    Analysis Summary: {post['post_summary']['summary']}
    Improvement Suggestions: {post['post_summary']['overall_suggestion']}
    
    POST TYPE: {'UGC' if 'ugc_analysis' in post else 'Official Brand Post'}
    
    TASK: Based on the analysis findings, create improved content that addresses the low-scoring areas.
    Focus on improving E-E-A-T-GEO factors (for official posts) or UGC engagement factors (for UGC posts).
    
    **CRITICAL INSTRUCTION: Your entire response MUST be in KOREAN and in Key-Value format with '|||' as separator.**
    
    Key-Value Format Example:
    new_caption_v1: (분석 결과를 반영한 개선된 캡션 버전 1)
    |||
    new_caption_v2: (다른 접근법의 개선된 캡션 버전 2)
    |||
    hashtags: #키준 #디자이너브랜드 #신상품 (새로운 컨셉에 최적화된 해시태그)
    |||
    new_image_idea: (분석 결과를 바탕으로 제안하는 새로운 이미지 컨셉 및 구성 아이디어)
    |||
    original_post_url: {post['post_url']}
    """
    
    try:
        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a creative director specializing in fashion brand content creation."},
                {"role": "user", "content": revision_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        revision_text = response.choices[0].message.content
        print(f"    🤖 LLM 개선안 생성 완료")
        
        # Key-Value 형식 파싱
        revision_data = {"original_post_url": post['post_url']}
        
        # '|||'로 분할하여 파싱
        pairs = revision_text.split('|||')
        for pair in pairs:
            if ':' in pair:
                key, value = pair.split(':', 1)
                key = key.strip()
                value = value.strip()
                revision_data[key] = value
        
        # 필수 키가 없으면 기본값 설정
        if 'new_caption_v1' not in revision_data:
            revision_data['new_caption_v1'] = "KIJUN 신상품 컬렉션 런칭! 세련된 디자인과 편안한 착용감을 동시에 만족시키는 프리미엄 의류 브랜드입니다. 💫"
        
        if 'hashtags' not in revision_data:
            revision_data['hashtags'] = "#키준 #KIJUN #디자이너브랜드 #신상품 #패션 #스타일 #프리미엄의류"
        
        if 'new_image_idea' not in revision_data:
            revision_data['new_image_idea'] = "Modern fashion lifestyle photography featuring KIJUN clothing in a minimalist Korean aesthetic setting"
        
        return revision_data
        
    except Exception as e:
        print(f"    ❌ LLM 개선안 생성 실패: {e}")
        # API 실패시 기본값 사용
        return {
            "new_caption_v1": "KIJUN 신상품 컬렉션 런칭! 세련된 디자인과 편안한 착용감을 동시에 만족시키는 프리미엄 의류 브랜드입니다. 💫",
            "hashtags": "#키준 #KIJUN #디자이너브랜드 #신상품 #패션 #스타일 #프리미엄의류",
            "new_image_idea": "Modern fashion lifestyle photography featuring KIJUN clothing in a minimalist Korean aesthetic setting",
            "original_post_url": post['post_url']
        }


def _analyze_success_factors(client, post):
    """상위 점수 게시물 성공 요인 분석"""
    print(f"  🏆 상위 점수 게시물 성공 요인 분석 중...")
    
    success_prompt = f"""
    You are a 'Lead Content Strategist' analyzing a high-performing KIJUN Instagram post.
    Identify the key success factors based on comprehensive performance analysis.
    
    HIGH-PERFORMING POST DATA:
    URL: {post['post_url']}
    Caption: {post['original_post_data']['content']}
    Excellent Score: {post['post_summary']['overall_score']}
    Analysis Summary: {post['post_summary']['summary']}
    
    POST TYPE: {'UGC' if 'ugc_analysis' in post else 'Official Brand Post'}
    
    TASK: Analyze WHY this post was highly effective and extract actionable insights.
    Focus on the strongest performing elements that can be replicated in future content.
    
    **CRITICAL INSTRUCTION: Your entire response MUST be in KOREAN and in Key-Value format with '|||' as separator.**
    
    Key-Value Format Example:
    success_factor_1: (가장 핵심적인 성공 요인 1)
    |||
    success_factor_2: (또 다른 중요한 성공 요인 2)
    |||
    key_takeaway: (이 게시물로부터 얻을 수 있는 가장 중요한 교훈과 다음 액션 아이템)
    |||
    original_post_url: {post['post_url']}
    """
    
    try:
        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a content strategist specializing in social media performance analysis."},
                {"role": "user", "content": success_prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        success_text = response.choices[0].message.content
        print(f"    🤖 LLM 성공 요인 분석 완료")
        
        # Key-Value 형식 파싱
        success_data = {"original_post_url": post['post_url']}
        
        # '|||'로 분할하여 파싱
        pairs = success_text.split('|||')
        for pair in pairs:
            if ':' in pair:
                key, value = pair.split(':', 1)
                key = key.strip()
                value = value.strip()
                success_data[key] = value
        
        return success_data
        
    except Exception as e:
        print(f"    ❌ LLM 성공 요인 분석 실패: {e}")
        # API 실패시 기본값 사용
        return {
            "success_factor_1": "우수한 시각적 구성과 브랜드 일관성",
            "success_factor_2": "효과적인 해시태그 활용과 타겟 오디언스 고려",
            "key_takeaway": "이 게시물의 성공 요소를 향후 콘텐츠에 적용 필요",
            "original_post_url": post['post_url']
        }