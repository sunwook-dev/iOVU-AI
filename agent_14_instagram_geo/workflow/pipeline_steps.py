"""
KIJUN Instagram 완전 통합 파이프라인 단계별 워크플로우
"""
import os
from utils.file_utils import (
    load_json_data, save_json_data, check_file_exists, 
    get_file_size_kb, ensure_directory_exists, extract_base_filename,
    get_ugc_type_from_filename
)
from tools.eeat_analyzer import EEATGeoAnalyzer
from tools.content_optimizer import ContentOptimizer
from tools.image_generator import ImageGenerator
from tools.mockup_generator import InstagramMockupGenerator


class InstagramAnalysisStep:
    """1단계: E-E-A-T-GEO 분석 단계"""
    
    def __init__(self, api_key):
        self.analyzer = EEATGeoAnalyzer(api_key)
        self.optimizer = ContentOptimizer(api_key)
    
    def execute(self, input_files=['kijun_official_tagged.json', 'kijun_official.json']):
        """E-E-A-T-GEO 분석 실행"""
        print(f"\n{'='*60}")
        print("1단계: KIJUN Instagram 상세 E-E-A-T-GEO 분석 시작")
        print(f"{'='*60}")
        
        # 단일 파일 처리 모드인지 확인
        if len(input_files) == 1:
            filename = input_files[0]
            print(f"📄 단일 파일 처리 모드: {filename}")
            processed_file = self._process_single_file(filename)
            if processed_file:
                return processed_file['content_file']
            else:
                return None
        
        # 다중 파일 처리 모드 (기존 방식)
        processed_files = []
        
        for filename in input_files:
            if not check_file_exists(filename):
                print(f"⚠️ {filename} 파일이 존재하지 않습니다.")
                continue
            
            processed_file = self._process_single_file(filename)
            if processed_file:
                processed_files.append(processed_file)
        
        if not processed_files:
            print(f"❌ 처리할 수 있는 파일이 없습니다.")
            return None
        
        print(f"\n🎉 전체 분석 완료!")
        print(f"=" * 60)
        print(f"📊 **처리 결과 요약**")
        
        for file_info in processed_files:
            print(f"📁 {file_info['input_file']} ({'UGC' if file_info['is_ugc'] else '공식'}):")
            print(f"  - 게시물 수: {file_info['post_count']}개")
            print(f"  - 분석 파일: {file_info['analysis_file']}")
            print(f"  - 콘텐츠 파일: {file_info['content_file']}")
        
        return processed_files[0]['content_file']
    
    def _process_single_file(self, filename):
        """단일 파일 처리"""
        try:
            print(f"\n🔄 {filename} 처리 시작...")
            
            data = load_json_data(filename)
            if not data:
                return None
            
            is_ugc_dataset = get_ugc_type_from_filename(filename)
            print(f"✅ 데이터 로드 성공: {filename} ({len(data)}개 게시물)")
            print(f"📋 데이터셋 유형: {'UGC 포함' if is_ugc_dataset else '공식 게시물 전용'}")
            
            detailed_analyses = []
            
            # 모든 게시물 분석
            for i, post in enumerate(data, 1):
                print(f"📝 게시물 {i}/{len(data)} 상세 분석 중...")
                
                analysis_result = self._analyze_post(post, i, is_ugc_dataset)
                if analysis_result:
                    detailed_analyses.append(analysis_result)
            
            # 콘텐츠 최적화 제안 생성
            content_suggestions = self._generate_content_suggestions(detailed_analyses)
            
            # 파일 저장
            return self._save_analysis_results(filename, detailed_analyses, content_suggestions, is_ugc_dataset)
            
        except Exception as e:
            print(f"❌ {filename} 처리 실패: {e}")
            return None
    
    def _analyze_post(self, post, post_number, is_ugc):
        """단일 게시물 분석"""
        try:
            print(f"  🤖 AI 상세 분석 중...")
            
            if is_ugc:
                analysis_json = self.analyzer.analyze_ugc_post(post)
            else:
                analysis_json = self.analyzer.analyze_official_post(post)
            
            if not analysis_json:
                return None
            
            # 분석 결과 구조화
            post_analysis = self._structure_analysis_result(post, post_number, analysis_json, is_ugc)
            
            print(f"  ✅ 완료 - 점수: {analysis_json.get('overall_score', 0):.1f}/100점")
            return post_analysis
            
        except Exception as e:
            print(f"  ❌ 분석 실패: {e}")
            return None
    
    def _structure_analysis_result(self, post, post_number, analysis_json, is_ugc):
        """분석 결과 구조화"""
        url = post.get('href', '')
        content = post.get('content', '')
        date = post.get('date', '')
        comments = post.get('comments', [])
        
        post_analysis = {
            "post_url": url,
            "original_post_data": {
                "number": post_number,
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
    
    def _generate_content_suggestions(self, detailed_analyses):
        """콘텐츠 개선 제안 생성"""
        sorted_analyses = sorted(detailed_analyses, key=lambda x: x['post_summary']['overall_score'])
        
        # 하위/상위 선택
        low_score_posts = sorted_analyses[:2] if len(sorted_analyses) >= 2 else sorted_analyses[:1]
        high_score_posts = sorted_analyses[-2:] if len(sorted_analyses) >= 2 else sorted_analyses[-1:]
        
        print(f"\n💡 개선된 콘텐츠 제안 생성 중...")
        
        low_score_revisions = []
        high_score_analyses = []
        
        # 하위 점수 게시물 개선안
        for post in low_score_posts:
            print(f"  📝 하위 점수 게시물 개선안 생성 중...")
            revision_json = self.optimizer.generate_content_revision(post)
            if revision_json:
                low_score_revisions.append(revision_json)
        
        # 상위 점수 게시물 성공 요인 분석
        for post in high_score_posts:
            print(f"  🏆 상위 점수 게시물 성공 요인 분석 중...")
            success_json = self.optimizer.analyze_success_factors(post)
            if success_json:
                high_score_analyses.append(success_json)
        
        return {
            "low_score_revisions": low_score_revisions,
            "high_score_analyses": high_score_analyses
        }
    
    def _save_analysis_results(self, filename, detailed_analyses, content_suggestions, is_ugc_dataset):
        """분석 결과 저장"""
        ugc_count = len([p for p in detailed_analyses if 'ugc_analysis' in p])
        has_ugc = ugc_count > 0
        
        print(f"\n📊 {filename} 분석 결과 구성:")
        print(f"  - 전체 게시물: {len(detailed_analyses)}개")
        print(f"  - UGC 게시물: {ugc_count}개")
        print(f"  - 공식 게시물: {len(detailed_analyses) - ugc_count}개")
        
        # 파일명 결정
        base_name = filename.replace('.json', '')
        if has_ugc:
            eeatg_filename = f'{base_name}_ugc_combined_analysis.json'
            content_filename = f'{base_name}_ugc_generated_content.json'
            print(f"💡 UGC 포함 분석으로 파일명: {eeatg_filename}")
        else:
            eeatg_filename = f'{base_name}_eeatg_analysis.json'
            content_filename = f'{base_name}_generated_content.json'
            print(f"💡 공식 게시물 전용 분석 파일명: {eeatg_filename}")
        
        # Always save to modular_agents/outputs directory
        from pathlib import Path
        current_file = Path(__file__)  # agent_14_instagram_geo/workflow/pipeline_steps.py
        modular_agents_dir = current_file.parent.parent.parent  # Go up to modular_agents
        output_path = modular_agents_dir / "outputs"
        output_path.mkdir(parents=True, exist_ok=True)
        
        eeatg_filepath = output_path / eeatg_filename
        content_filepath = output_path / content_filename
        
        # 파일 저장
        save_json_data(detailed_analyses, str(eeatg_filepath))
        save_json_data(content_suggestions, str(content_filepath))
        
        print(f"✅ {filename} 처리 완료 - 파일 저장: {eeatg_filename}, {content_filename}")
        
        return {
            'input_file': filename,
            'analysis_file': eeatg_filename,
            'content_file': content_filename,
            'is_ugc': is_ugc_dataset,
            'post_count': len(detailed_analyses)
        }


class ImageGenerationStep:
    """2단계: 이미지 생성 단계"""
    
    def __init__(self, api_key):
        self.generator = ImageGenerator(api_key)
    
    def execute(self, content_filename):
        """이미지 생성 실행"""
        print(f"\n{'='*60}")
        print("2단계: 저장된 아이디어로 최종 이미지 생성")
        print(f"{'='*60}")
        
        try:
            data = load_json_data(content_filename)
            if not data:
                return None
            
            low_score_revisions = data.get('low_score_revisions', [])
            
            if not low_score_revisions:
                print("⚠️ low_score_revisions 데이터를 찾을 수 없습니다.")
                return None
            
            # 첫 번째 항목으로 이미지 생성
            draft = low_score_revisions[0]
            print(f"📝 이미지 생성 대상: {draft.get('original_post_url', 'Unknown')}")
            
            image_generation_prompt = draft.get('new_image_idea', '')
            
            if image_generation_prompt:
                return self.generator.generate_image_from_idea(image_generation_prompt)
            else:
                print("❌ new_image_idea를 찾을 수 없습니다.")
                return None
                
        except Exception as e:
            print(f"❌ 이미지 생성 실패: {e}")
            return None


class MockupGenerationStep:
    """3단계: Instagram 목업 생성 단계"""
    
    def __init__(self, images_folder="./images"):
        self.generator = InstagramMockupGenerator(images_folder)
    
    def execute(self, image_path, content_filename):
        """목업 생성 실행 - UGC/비-UGC 별도 처리"""
        print(f"\n{'='*60}")
        print("3단계: Instagram 게시물 목업 생성")
        print(f"{'='*60}")
        
        try:
            # 처리된 파일명에서 기본 이름 추출
            base_filename = extract_base_filename(content_filename)
            
            # JSON 데이터 로드
            data = load_json_data(content_filename)
            if not data:
                return None
            
            mockup_paths = []
            
            # UGC 데이터 확인
            is_ugc_content = 'ugc' in content_filename.lower()
            
            if is_ugc_content:
                print("📱 UGC 콘텐츠 목업 생성...")
                # UGC 전용 목업 생성
                mockup_path = self._create_ugc_mockup(data, base_filename, image_path)
                if mockup_path:
                    mockup_paths.append(mockup_path)
            else:
                print("📱 공식 콘텐츠 목업 생성...")
                # 공식 콘텐츠 전용 목업 생성
                mockup_path = self._create_official_mockup(data, base_filename, image_path)
                if mockup_path:
                    mockup_paths.append(mockup_path)
            
            print(f"✅ 총 {len(mockup_paths)}개의 목업이 생성되었습니다.")
            return mockup_paths[0] if mockup_paths else None
            
        except Exception as e:
            print(f"❌ Instagram 목업 생성 실패: {e}")
            return None
    
    def _create_ugc_mockup(self, data, base_filename, image_path):
        """UGC 전용 목업 생성"""
        try:
            caption_data = data['low_score_revisions'][0]
            # UGC는 더 개인적인 v2 캡션 선택
            caption_text = caption_data.get('new_caption_v2', caption_data.get('new_caption_v1', ''))
            hashtags_text = caption_data['hashtags']
            
            # UGC 목업 파일명 - modular_agents/outputs에 저장
            from pathlib import Path
            current_file = Path(__file__)  # agent_14_instagram_geo/workflow/pipeline_steps.py
            modular_agents_dir = current_file.parent.parent.parent  # Go up to modular_agents
            output_path = modular_agents_dir / "outputs"
            output_path.mkdir(parents=True, exist_ok=True)
            output_filename = str(output_path / f"{base_filename}_ugc_instagram_mockup.jpg")
            
            # UGC용 계정명과 스타일 설정
            return self.generator.create_mockup(
                image_path or "dummy.jpg", 
                caption_text, 
                hashtags_text, 
                output_filename,
                account_name="tomncheese",  # UGC 계정명
                account_type="ugc"
            )
        except Exception as e:
            print(f"❌ UGC 목업 생성 실패: {e}")
            return None
    
    def _create_official_mockup(self, data, base_filename, image_path):
        """공식 콘텐츠 전용 목업 생성"""
        try:
            caption_data = data['low_score_revisions'][0]
            # 공식은 더 브랜드적인 v1 캡션 선택
            caption_text = caption_data.get('new_caption_v1', caption_data.get('new_caption_v2', ''))
            hashtags_text = caption_data['hashtags']
            
            # 공식 목업 파일명 - modular_agents/outputs에 저장
            from pathlib import Path
            current_file = Path(__file__)  # agent_14_instagram_geo/workflow/pipeline_steps.py
            modular_agents_dir = current_file.parent.parent.parent  # Go up to modular_agents
            output_path = modular_agents_dir / "outputs"
            output_path.mkdir(parents=True, exist_ok=True)
            output_filename = str(output_path / f"{base_filename}_official_instagram_mockup.jpg")
            
            # 공식 계정명과 스타일 설정
            return self.generator.create_mockup(
                image_path or "dummy.jpg", 
                caption_text, 
                hashtags_text, 
                output_filename,
                account_name="kijun_official",  # 공식 계정명
                account_type="official"
            )
        except Exception as e:
            print(f"❌ 공식 목업 생성 실패: {e}")
            return None
