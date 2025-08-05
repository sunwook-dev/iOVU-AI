"""
KIJUN Instagram DB 기반 파이프라인
- DB에서 Instagram 데이터 불러오기
- 공식/UGC 게시물 구분 처리
- E-E-A-T-GEO 분석 및 보고서 생성
- 결과를 modular_agents/outputs/에 저장
"""
import os
import json
import sys
import requests
from PIL import Image, ImageDraw, ImageFont
import textwrap
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

# 현재 파일의 위치: agent_14_instagram_geo/kijun_db_pipeline.py
# 목표: modular_agents/database/utils/connection.py
current_dir = Path(__file__).parent  # agent_14_instagram_geo
modular_agents_dir = current_dir.parent  # modular_agents

# 직접 database connection 파일을 import
import importlib.util
connection_path = modular_agents_dir / "database" / "utils" / "connection.py"
spec = importlib.util.spec_from_file_location("connection", connection_path)
connection_module = importlib.util.module_from_spec(spec)

# database config도 필요하므로 추가
config_path = modular_agents_dir / "database" / "config.py"
config_spec = importlib.util.spec_from_file_location("config", config_path)
config_module = importlib.util.module_from_spec(config_spec)
config_spec.loader.exec_module(config_module)

# connection 모듈에서 config를 사용할 수 있도록 설정
sys.modules['config'] = config_module
spec.loader.exec_module(connection_module)

get_db = connection_module.get_db

# 환경 변수 로드
load_dotenv()

def get_korean_font(size=24):
    """한글 폰트 가져오기 (Windows, Mac 지원)"""
    try:
        import platform
        system = platform.system()
        
        if system == 'Windows':
            font_paths = [
                "C:/Windows/Fonts/malgun.ttf",      # 맑은 고딕
                "C:/Windows/Fonts/malgunbd.ttf",    # 맑은 고딕 Bold
                "C:/Windows/Fonts/gulim.ttc",       # 굴림
            ]
        elif system == 'Darwin':  # Mac
            font_paths = [
                "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                "/Library/Fonts/AppleGothic.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]
        else:  # Linux
            font_paths = [
                "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, size)
                    print(f"✅ 한글 폰트 발견: {os.path.basename(font_path)}")
                    return font
            except:
                continue
        
        print("⚠️ 시스템 한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
        return ImageFont.load_default()
        
    except Exception as e:
        print(f"⚠️ 폰트 로딩 오류: {e}")
        return ImageFont.load_default()

def load_instagram_data_from_db(brand_name='kijun'):
    """DB에서 Instagram 데이터 불러오기"""
    print(f"\n📊 DB에서 {brand_name} Instagram 데이터 불러오기")
    
    try:
        db = get_db()
        
        # 공식 게시물 조회
        official_posts = db.execute("""
            SELECT post_id, post_url, caption, hashtags, mentions, 
                   like_count, comment_count, posted_at, content_type,
                   media_urls, thumbnail_url
            FROM 03_raw_instagram_data 
            WHERE brand_name = %s AND content_type = 'official'
            ORDER BY posted_at DESC
        """, (brand_name,))
        
        # UGC 게시물 조회
        ugc_posts = db.execute("""
            SELECT post_id, post_url, caption, hashtags, mentions, 
                   like_count, comment_count, posted_at, content_type,
                   media_urls, thumbnail_url
            FROM 03_raw_instagram_data 
            WHERE brand_name = %s AND content_type = 'ugc'
            ORDER BY posted_at DESC
        """, (brand_name,))
        
        print(f"✅ 공식 게시물: {len(official_posts)}개")
        print(f"✅ UGC 게시물: {len(ugc_posts)}개")
        
        # JSON 형태로 변환
        def convert_db_to_json(posts):
            converted = []
            for post in posts:
                try:
                    # JSON 필드 파싱
                    hashtags = json.loads(post['hashtags']) if post['hashtags'] else []
                    mentions = json.loads(post['mentions']) if post['mentions'] else []
                    media_urls = json.loads(post['media_urls']) if post['media_urls'] else []
                    
                    converted_post = {
                        'href': post['post_url'],
                        'post_id': post['post_id'],
                        'content': post['caption'] or '',
                        'date': post['posted_at'].strftime('%Y-%m-%d') if post['posted_at'] else '',
                        'like_count': post['like_count'] or 0,
                        'comment_count': post['comment_count'] or 0,
                        'hashtags': hashtags,
                        'mentions': mentions,
                        'img': media_urls,
                        'comments': [],  # 실제 댓글 데이터는 별도 수집 필요
                        'content_type': post['content_type']
                    }
                    converted.append(converted_post)
                except Exception as e:
                    print(f"⚠️ 게시물 변환 오류: {e}")
                    continue
            return converted
        
        official_data = convert_db_to_json(official_posts)
        ugc_data = convert_db_to_json(ugc_posts)
        
        return official_data, ugc_data
        
    except Exception as e:
        print(f"❌ DB 데이터 로드 실패: {e}")
        return [], []

def analyze_posts_with_llm(posts_data, is_ugc=False):
    """LLM을 사용한 게시물 분석"""
    print(f"\n🤖 {'UGC' if is_ugc else '공식'} 게시물 LLM 분석 시작")
    
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API 키가 .env 파일에 설정되지 않았습니다.")
        return []
    
    client = OpenAI(api_key=api_key)
    detailed_analyses = []
    
    for i, post in enumerate(posts_data, 1):
        print(f"📝 게시물 {i}/{len(posts_data)} 분석 중...")
        
        url = post.get('href', '')
        content = post.get('content', '')
        date = post.get('date', '')
        like_count = post.get('like_count', 0)
        comment_count = post.get('comment_count', 0)
        
        print(f"  📍 URL: {url[:50]}...")
        print(f"  💖 좋아요: {like_count}, 💬 댓글: {comment_count}")
        
        if is_ugc:
            # UGC 분석 프롬프트
            analysis_prompt = f"""
            You are a 'Senior Marketing Strategist' analyzing a KIJUN brand UGC Instagram post.
            Perform comprehensive analysis and provide scoring.
            
            POST DATA:
            URL: {url}
            Caption: {content}
            Date: {date}
            Likes: {like_count}
            Comments: {comment_count}
            
            Analyze TPO (Time, Place, Occasion), styling creativity, and user sentiment.
            
            Provide analysis in JSON format with Korean explanations:
            {{
                "product_analysis": "제품 분석",
                "tpo_score": 점수 (0-100),
                "tpo_reason": "TPO 적절성 분석",
                "styling_score": 점수 (0-100),
                "styling_reason": "스타일링 창의성 분석",
                "sentiment_score": 점수 (0-100),
                "sentiment_reason": "사용자 감정 및 만족도 분석",
                "brand_relevance": 점수 (0-100),
                "brand_reason": "브랜드 연관성 분석",
                "visual_appeal": 점수 (0-100),
                "visual_reason": "시각적 매력도 분석",
                "overall_score": 평균점수 (0-100),
                "summary": "전체 요약",
                "improvement_suggestions": "개선 제안"
            }}
            """
        else:
            # 공식 게시물 E-E-A-T-GEO 분석 프롬프트
            analysis_prompt = f"""
            You are a 'Senior Digital Marketing Analyst' analyzing official KIJUN Instagram content.
            Perform comprehensive E-E-A-T-GEO analysis.
            
            POST DATA:
            URL: {url}
            Caption: {content}
            Date: {date}
            Likes: {like_count}
            Comments: {comment_count}
            
            ANALYSIS FRAMEWORK (E-E-A-T-GEO):
            - Experience: User experience quality
            - Expertise: Fashion expertise demonstration  
            - Authoritativeness: Brand authority signals
            - Trustworthiness: Content credibility
            - Geographic: Location/cultural relevance
            
            Provide analysis in JSON format with Korean explanations:
            {{
                "experience_score": 점수 (0-100),
                "experience_reason": "사용자 경험 품질 분석",
                "expertise_score": 점수 (0-100),
                "expertise_reason": "패션 전문성 분석",
                "authoritativeness_score": 점수 (0-100),
                "authoritativeness_reason": "브랜드 권위성 분석",
                "trustworthiness_score": 점수 (0-100),
                "trustworthiness_reason": "콘텐츠 신뢰성 분석",
                "geographic_score": 점수 (0-100),
                "geographic_reason": "지리적/문화적 연관성 분석",
                "overall_score": 평균점수 (0-100),
                "summary": "E-E-A-T-GEO 전체 분석 요약",
                "improvement_suggestions": "콘텐츠 개선 제안"
            }}
            """
        
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
            
            # JSON 파싱
            try:
                import re
                json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                json_matches = re.findall(json_pattern, analysis_text, re.DOTALL)
                
                if json_matches:
                    json_text = max(json_matches, key=len)
                    analysis_json = json.loads(json_text)
                else:
                    json_start = analysis_text.find('{')
                    json_end = analysis_text.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        json_text = analysis_text[json_start:json_end]
                        analysis_json = json.loads(json_text)
                    else:
                        raise ValueError("JSON 형식을 찾을 수 없습니다.")
                        
            except Exception as json_error:
                print(f"  ⚠️ JSON 파싱 실패 - 기본값 사용")
                analysis_json = {
                    "overall_score": 75,
                    "summary": f"게시물 {i} 분석 완료 (파싱 오류)",
                    "improvement_suggestions": "분석 데이터 확인 필요"
                }
            
        except Exception as e:
            print(f"  ❌ LLM 분석 실패: {e}")
            analysis_json = {
                "overall_score": 75,
                "summary": f"게시물 {i} 분석 오류",
                "improvement_suggestions": "분석 재시도 필요"
            }
        
        post_analysis = {
            "post_data": post,
            "analysis": analysis_json,
            "content_type": post.get('content_type', 'official')
        }
        
        detailed_analyses.append(post_analysis)
        score = analysis_json.get('overall_score', 75)
        print(f"  ✅ 완료 - 점수: {score}/100점")
    
    return detailed_analyses

def generate_improvement_suggestions(low_score_posts):
    """하위 점수 게시물에 대한 개선안 생성"""
    print(f"\n💡 하위 점수 게시물 개선안 생성 중...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return []
    
    client = OpenAI(api_key=api_key)
    suggestions = []
    
    for post in low_score_posts:
        post_data = post['post_data']
        analysis = post['analysis']
        
        revision_prompt = f"""
        You are a senior Creative Director for KIJUN fashion brand.
        Create improved content for an underperforming Instagram post.
        
        ORIGINAL POST:
        Caption: {post_data.get('content', '')}
        Score: {analysis.get('overall_score', 0)}
        Issues: {analysis.get('improvement_suggestions', '')}
        
        Create improved content in Korean Key-Value format with '|||' separator:
        
        new_caption_v1: (개선된 캡션 버전 1)
        |||
        new_caption_v2: (개선된 캡션 버전 2)
        |||
        hashtags: #키준 #KIJUN #패션 #스타일 (최적화된 해시태그)
        |||
        new_image_idea: (새로운 이미지 컨셉 아이디어)
        |||
        improvement_focus: (주요 개선 포인트)
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a creative director specializing in fashion brand content."},
                    {"role": "user", "content": revision_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            revision_text = response.choices[0].message.content
            
            # Key-Value 형식 파싱
            revision_data = {"original_post_url": post_data.get('href', '')}
            
            pairs = revision_text.split('|||')
            for pair in pairs:
                if ':' in pair:
                    key, value = pair.split(':', 1)
                    revision_data[key.strip()] = value.strip()
            
            # 기본값 설정
            if 'new_caption_v1' not in revision_data:
                revision_data['new_caption_v1'] = "KIJUN의 새로운 컬렉션을 만나보세요! 세련된 디자인과 편안한 착용감이 조화를 이룬 프리미엄 패션을 경험해보세요. ✨"
            
            if 'hashtags' not in revision_data:
                revision_data['hashtags'] = "#키준 #KIJUN #패션 #스타일 #신상품 #프리미엄"
            
            suggestions.append(revision_data)
            
        except Exception as e:
            print(f"    ❌ 개선안 생성 실패: {e}")
            suggestions.append({
                "new_caption_v1": "KIJUN의 새로운 컬렉션을 만나보세요!",
                "hashtags": "#키준 #KIJUN #패션",
                "original_post_url": post_data.get('href', '')
            })
    
    return suggestions

def create_output_directory():
    """modular_agents/outputs 디렉토리 생성"""
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir

def main():
    """메인 실행 함수"""
    print("🚀 KIJUN Instagram DB 기반 분석 파이프라인 시작")
    print("=" * 60)
    
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API 키가 .env 파일에 설정되지 않았습니다.")
        return False
    
    # 출력 디렉토리 생성
    output_dir = create_output_directory()
    print(f"📁 출력 디렉토리: {output_dir}")
    
    try:
        # 1. DB에서 데이터 불러오기
        official_posts, ugc_posts = load_instagram_data_from_db('kijun')
        
        if not official_posts and not ugc_posts:
            print("❌ DB에서 Instagram 데이터를 찾을 수 없습니다.")
            return False
        
        # 2. 공식 게시물 분석
        official_analyses = []
        if official_posts:
            official_analyses = analyze_posts_with_llm(official_posts, is_ugc=False)
        
        # 3. UGC 게시물 분석
        ugc_analyses = []
        if ugc_posts:
            ugc_analyses = analyze_posts_with_llm(ugc_posts, is_ugc=True)
        
        # 4. 통합 분석 결과 생성
        all_analyses = official_analyses + ugc_analyses
        
        # 점수별 정렬
        sorted_analyses = sorted(all_analyses, key=lambda x: x['analysis']['overall_score'])
        
        # 하위/상위 게시물 선별
        low_score_posts = sorted_analyses[:2] if len(sorted_analyses) >= 2 else sorted_analyses
        high_score_posts = sorted_analyses[-2:] if len(sorted_analyses) >= 2 else sorted_analyses
        
        # 5. 개선안 생성
        improvement_suggestions = generate_improvement_suggestions(low_score_posts)
        
        # 6. 결과 저장
        timestamp = Path(__file__).name.replace('.py', '')
        
        # 전체 분석 결과
        analysis_result = {
            "analysis_summary": {
                "total_posts": len(all_analyses),
                "official_posts": len(official_analyses),
                "ugc_posts": len(ugc_analyses),
                "average_score": sum(a['analysis']['overall_score'] for a in all_analyses) / len(all_analyses) if all_analyses else 0
            },
            "detailed_analyses": all_analyses,
            "low_score_posts": low_score_posts,
            "high_score_posts": high_score_posts,
            "improvement_suggestions": improvement_suggestions
        }
        
        # 파일 저장
        analysis_file = output_dir / f"kijun_instagram_db_analysis_{timestamp}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n✅ 분석 완료!")
        print(f"📊 분석 결과: {analysis_file}")
        print(f"📈 총 게시물: {len(all_analyses)}개")
        print(f"📈 평균 점수: {analysis_result['analysis_summary']['average_score']:.1f}점")
        
        return True
        
    except Exception as e:
        print(f"❌ 파이프라인 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()