"""
E-E-A-T-GEO 분석기
"""
import json
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from openai import OpenAI
from utils.file_utils import load_json_data, save_json_data
from utils.text_utils import parse_key_value_output


class EEATAnalyzer:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
    
    def analyze_posts(self, input_files):
        """게시물 분석 실행"""
        processed_files = []
        
        for filename in input_files:
            if not self._file_exists(filename):
                print(f"⚠️ {filename} 파일이 존재하지 않습니다.")
                continue
                
            try:
                print(f"\n🔄 {filename} 처리 시작...")
                
                data = load_json_data(filename)
                if not data:
                    continue
                
                is_ugc_dataset = 'tagged' in filename.lower()
                print(f"✅ 데이터 로드 성공: {filename} ({len(data)}개 게시물)")
                print(f"📋 데이터셋 유형: {'UGC 포함' if is_ugc_dataset else '공식 게시물 전용'}")
                
                detailed_analyses = []
                
                # 모든 게시물 분석
                for i, post in enumerate(data, 1):
                    print(f"📝 게시물 {i}/{len(data)} 상세 분석 중...")
                    
                    analysis_result = self._analyze_single_post(post, i, is_ugc_dataset)
                    if analysis_result:
                        detailed_analyses.append(analysis_result)
                        print(f"  ✅ 완료 - 점수: {analysis_result['post_summary']['overall_score']:.1f}/100점")
                    else:
                        print(f"  ❌ 분석 실패")
                        continue
                
                # 분석 결과 처리 및 저장
                file_info = self._process_and_save_analysis(filename, detailed_analyses, is_ugc_dataset)
                if file_info:
                    processed_files.append(file_info)
                
            except Exception as e:
                print(f"❌ {filename} 처리 실패: {e}")
                continue
        
        return processed_files[0]['content_file'] if processed_files else None
    
    def _file_exists(self, filename):
        """파일 존재 확인"""
        import os
        return os.path.exists(filename)
    
    def _analyze_single_post(self, post, index, is_ugc):
        """단일 게시물 분석"""
        url = post.get('href', '')
        content = post.get('content', '')
        date = post.get('date', '')
        comments = post.get('comments', [])
        
        print(f"  📍 URL: {url[:50]}...")
        print(f"  🏷️ 타입: {'UGC' if is_ugc else '공식 게시물'}")
        
        if is_ugc:
            analysis_prompt = self._get_ugc_analysis_prompt(url, content, date, len(comments))
        else:
            analysis_prompt = self._get_official_analysis_prompt(url, content, date, len(comments))
        
        try:
            print(f"  🤖 AI 상세 분석 중...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            
            # JSON 추출
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                analysis_json = json.loads(analysis_text[start_idx:end_idx])
            else:
                raise ValueError("JSON을 찾을 수 없습니다")
            
            # 구조화된 분석 결과 생성
            return self._structure_analysis_result(post, index, analysis_json, is_ugc, url, date, content, comments)
            
        except Exception as e:
            print(f"  ❌ 분석 실패: {e}")
            return None
    
    def _get_ugc_analysis_prompt(self, url, content, date, comment_count):
        """UGC 분석 프롬프트"""
        return f"""
        You are a 'Senior Marketing Strategist' analyzing a KIJUN brand UGC Instagram post.
        Perform a comprehensive 3-step analysis and provide final scoring.
        
        POST DATA:
        URL: {url}
        Caption: {content}
        Date: {date}
        Comments: {comment_count}
        
        STEP 1 - Product & TPO Analysis:
        From the image and caption, identify the KIJUN product and analyze the TPO (Time, Place, Occasion).
        Score how well the product fits the TPO situation (0-100 points, where 100 is perfect fit).
        
        STEP 2 - Styling Analysis:
        Define the styling mood, list paired items, and score the styling creativity (0-100 points).
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
    
    def _get_official_analysis_prompt(self, url, content, date, comment_count):
        """공식 게시물 분석 프롬프트"""
        return f"""
        You are a content quality inspector for the fashion brand 'KIJUN', specializing in E-E-A-T and Generative Engine Optimization (GEO).
        Analyze this official KIJUN Instagram post comprehensively.
        
        POST DATA:
        URL: {url}
        Caption: {content}
        Date: {date}
        Comments: {comment_count}
        
        [KIJUN E-E-A-T-GEO Analysis Framework]
        
        **SCORING INSTRUCTIONS: Use 0-100 point scale for ALL scores where:**
        - 90-100: Exceptional quality, industry-leading standard
        - 80-89: Very good quality, above average performance  
        - 70-79: Good quality, meets standard expectations
        - 60-69: Fair quality, some improvement needed
        - 50-59: Below average, significant improvement required
        - 0-49: Poor quality, major overhaul needed
        
        1. **Experience (0-100 points)**: Does this content show real user experience or authentic brand experience?
        2. **Expertise (0-100 points)**: Does this content demonstrate professional fashion knowledge and brand expertise?
        3. **Authoritativeness (0-100 points)**: Does this content align with KIJUN's brand authority and aesthetic consistency?
        4. **Trustworthiness (0-100 points)**: Is this content authentic, reliable, and free from exaggeration?
        
        5. **GEO (Generative Engine Optimization) - Detailed Breakdown (Each 0-100 points)**:
           - **Clarity & Specificity**: How clear and specific are product names, keywords, and information?
           - **Structured Information**: Is information well-structured for AI parsing (bullet points, clear hierarchy)?
           - **Contextual Richness**: Does it provide rich context (collection info, styling tips, season relevance)?
           - **Visual-Text Alignment**: Do images and text strongly support each other?
           - **Timeliness & Event-Relevance**: Is content relevant to current time, season, or events?
           - **Originality**: Is the creative expression fresh, unique, and avoiding clichés?
        
        6. **Content Synergy Analysis (Each 0-100 points)**:
           - **Visual Coherence**: Consistency in mood, color palette, and style across all images
           - **Narrative Flow**: Logical sequence and storytelling flow of images
           - **Alignment with Caption**: How well caption unifies and enhances all visuals
        
        Provide comprehensive analysis in JSON format with Korean explanations:
        {{
            "experience_score": 점수 (0-100),
            "experience_reason": "실제 경험 기반 콘텐츠 여부와 사용자 관점 반영도 분석",
            "expertise_score": 점수 (0-100),
            "expertise_reason": "패션 전문성과 브랜드 노하우 전달력 분석",
            "authoritativeness_score": 점수 (0-100),
            "authoritativeness_reason": "브랜드 권위성과 일관된 미적 기준 유지도 분석",
            "trustworthiness_score": 점수 (0-100),
            "trustworthiness_reason": "신뢰성과 정보의 정확성, 과장 없는 표현 분석",
            "geo_clarity_score": 점수 (0-100),
            "geo_clarity_reason": "제품명, 키워드의 명확성과 AI 이해도 분석",
            "geo_structure_score": 점수 (0-100),
            "geo_structure_reason": "정보 구조화와 AI 파싱 용이성 분석",
            "geo_context_score": 점수 (0-100),
            "geo_context_reason": "컨텍스트 풍부성과 활용 맥락 제공도 분석",
            "geo_alignment_score": 점수 (0-100),
            "geo_alignment_reason": "이미지-텍스트 정합성과 상호 보완성 분석",
            "geo_timeliness_score": 점수 (0-100),
            "geo_timeliness_reason": "시의성과 계절감, 이벤트 연관성 분석",
            "geo_originality_score": 점수 (0-100),
            "geo_originality_reason": "창의적 표현과 독창성, 차별화 요소 분석",
            "visual_coherence_score": 점수 (0-100),
            "visual_coherence_reason": "이미지 간 시각적 일관성과 통일감 분석",
            "narrative_flow_score": 점수 (0-100),
            "narrative_flow_reason": "서사적 흐름과 이미지 순서의 논리성 분석",
            "alignment_with_caption_score": 점수 (0-100),
            "alignment_with_caption_reason": "캡션과 이미지의 연결성과 메시지 통합도 분석",
            "overall_score": 전체 평균점수 (0-100),
            "category_averages": {{
                "eeat_avg": "E-E-A-T 4개 항목 평균",
                "geo_avg": "GEO 6개 항목 평균", 
                "synergy_avg": "시너지 3개 항목 평균"
            }},
            "summary": "전체 분석 요약과 브랜드 콘텐츠로서의 가치 평가",
            "overall_suggestion": "구체적이고 실행 가능한 개선 제안사항"
        }}
        """
    
    def _structure_analysis_result(self, post, index, analysis_json, is_ugc, url, date, content, comments):
        """분석 결과 구조화"""
        post_analysis = {
            "post_url": url,
            "original_post_data": {
                "number": index,
                "href": url,
                "date": date,
                "content": content,
                "img": post.get('img', []),
                "comments": comments
            },
            "post_summary": {
                "summary": analysis_json.get('summary', ''),
                "overall_score": analysis_json.get('overall_score', 0),
                "category_averages": analysis_json.get('category_averages', {}),
                "overall_suggestion": analysis_json.get('overall_suggestion', '')
            }
        }
        
        # UGC와 공식 게시물에 따른 다른 구조
        if is_ugc:
            post_analysis["ugc_analysis"] = {
                "product_guess": analysis_json.get('product_guess', ''),
                "tpo_analysis": analysis_json.get('tpo_analysis', ''),
                "tpo_score": str(analysis_json.get('tpo_score', 0)),
                "tpo_reason": analysis_json.get('tpo_reason', ''),
                "styling_mood": analysis_json.get('styling_mood', ''),
                "paired_items": analysis_json.get('paired_items', ''),
                "styling_score": str(analysis_json.get('styling_score', 0)),
                "styling_reason": analysis_json.get('styling_reason', ''),
                "sentiment_score": str(analysis_json.get('sentiment_score', 0)),
                "sentiment_reason": analysis_json.get('sentiment_reason', ''),
                "brand_relevance": str(analysis_json.get('brand_relevance', 0)),
                "brand_reason": analysis_json.get('brand_reason', ''),
                "visual_appeal": str(analysis_json.get('visual_appeal', 0)),
                "visual_reason": analysis_json.get('visual_reason', ''),
                "synergy_score": str(analysis_json.get('synergy_score', 0)),
                "synergy_reason": analysis_json.get('synergy_reason', '')
            }
        else:
            post_analysis["synergy_analysis"] = {
                "visual_coherence_score": str(analysis_json.get('visual_coherence_score', 0)),
                "visual_coherence_reason": analysis_json.get('visual_coherence_reason', ''),
                "narrative_flow_score": str(analysis_json.get('narrative_flow_score', 0)),
                "narrative_flow_reason": analysis_json.get('narrative_flow_reason', ''),
                "alignment_with_caption_score": str(analysis_json.get('alignment_with_caption_score', 0)),
                "alignment_with_caption_reason": analysis_json.get('alignment_with_caption_reason', '')
            }
            
            post_analysis["eeat_geo_analysis"] = {
                "experience_score": str(analysis_json.get('experience_score', 0)),
                "experience_reason": analysis_json.get('experience_reason', ''),
                "expertise_score": str(analysis_json.get('expertise_score', 0)),
                "expertise_reason": analysis_json.get('expertise_reason', ''),
                "authoritativeness_score": str(analysis_json.get('authoritativeness_score', 0)),
                "authoritativeness_reason": analysis_json.get('authoritativeness_reason', ''),
                "trustworthiness_score": str(analysis_json.get('trustworthiness_score', 0)),
                "trustworthiness_reason": analysis_json.get('trustworthiness_reason', ''),
                "geo_clarity_score": str(analysis_json.get('geo_clarity_score', 0)),
                "geo_clarity_reason": analysis_json.get('geo_clarity_reason', ''),
                "geo_structure_score": str(analysis_json.get('geo_structure_score', 0)),
                "geo_structure_reason": analysis_json.get('geo_structure_reason', ''),
                "geo_context_score": str(analysis_json.get('geo_context_score', 0)),
                "geo_context_reason": analysis_json.get('geo_context_reason', ''),
                "geo_alignment_score": str(analysis_json.get('geo_alignment_score', 0)),
                "geo_alignment_reason": analysis_json.get('geo_alignment_reason', ''),
                "geo_timeliness_score": str(analysis_json.get('geo_timeliness_score', 0)),
                "geo_timeliness_reason": analysis_json.get('geo_timeliness_reason', ''),
                "geo_originality_score": str(analysis_json.get('geo_originality_score', 0)),
                "geo_originality_reason": analysis_json.get('geo_originality_reason', '')
            }
        
        post_analysis["individual_analyses"] = [{
            "overall_suggestion": analysis_json.get('overall_suggestion', '')
        }]
        
        return post_analysis
    
    def _process_and_save_analysis(self, filename, detailed_analyses, is_ugc_dataset):
        """분석 결과 처리 및 저장"""
        # 점수별 정렬 및 콘텐츠 생성
        sorted_analyses = sorted(detailed_analyses, key=lambda x: x['post_summary']['overall_score'])
        
        # 하위/상위 선택
        low_score_posts = sorted_analyses[:2] if len(sorted_analyses) >= 2 else sorted_analyses[:1]
        high_score_posts = sorted_analyses[-2:] if len(sorted_analyses) >= 2 else sorted_analyses[-1:]
        
        print(f"\n🎯 {filename} 분석 완료!")
        print(f"📊 총 {len(detailed_analyses)}개 게시물 분석")
        
        # 개선된 콘텐츠 생성
        print(f"\n💡 {filename} 개선된 콘텐츠 제안 생성 중...")
        
        low_score_revisions = self._generate_content_revisions(low_score_posts)
        high_score_analyses = self._generate_success_analyses(high_score_posts)
        
        # UGC 포함 여부 확인
        ugc_count = len([p for p in detailed_analyses if 'ugc_analysis' in p])
        has_ugc = ugc_count > 0
        
        print(f"\n📊 {filename} 분석 결과 구성:")
        print(f"  - 전체 게시물: {len(detailed_analyses)}개")
        print(f"  - UGC 게시물: {ugc_count}개")
        print(f"  - 공식 게시물: {len(detailed_analyses) - ugc_count}개")
        
        # 파일명 결정
        base_name = filename.replace('.json', '')
        if has_ugc:
            eeatg_filename = os.path.join('output', f'{base_name}_ugc_combined_analysis.json')
            content_filename = os.path.join('output', f'{base_name}_ugc_generated_content.json')
            print(f"💡 UGC 포함 분석으로 파일명: {eeatg_filename}")
        else:
            eeatg_filename = os.path.join('output', f'{base_name}_eeatg_analysis.json')
            content_filename = os.path.join('output', f'{base_name}_generated_content.json')
            print(f"💡 공식 게시물 전용 분석 파일명: {eeatg_filename}")
        
        # 파일 저장
        save_json_data(detailed_analyses, eeatg_filename)
        
        content_suggestions = {
            "low_score_revisions": low_score_revisions,
            "high_score_analyses": high_score_analyses
        }
        save_json_data(content_suggestions, content_filename)
        
        print(f"✅ {filename} 처리 완료 - 파일 저장: {eeatg_filename}, {content_filename}")
        
        return {
            'input_file': filename,
            'analysis_file': eeatg_filename,
            'content_file': content_filename,
            'is_ugc': is_ugc_dataset,
            'post_count': len(detailed_analyses)
        }
    
    def _generate_content_revisions(self, low_score_posts):
        """하위 점수 게시물 개선안 생성"""
        revisions = []
        
        for post in low_score_posts:
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
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": revision_prompt}],
                    temperature=0.5
                )
                
                revision_text = response.choices[0].message.content
                revision_json = parse_key_value_output(revision_text)
                if revision_json:
                    revisions.append(revision_json)
                
            except Exception as e:
                print(f"    ❌ 개선안 생성 실패: {e}")
        
        return revisions
    
    def _generate_success_analyses(self, high_score_posts):
        """상위 점수 게시물 성공 요인 분석"""
        analyses = []
        
        for post in high_score_posts:
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
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": success_prompt}],
                    temperature=0.5
                )
                
                success_text = response.choices[0].message.content
                success_json = parse_key_value_output(success_text)
                if success_json:
                    analyses.append(success_json)
                
            except Exception as e:
                print(f"    ❌ 성공 요인 분석 실패: {e}")
        
        return analyses
