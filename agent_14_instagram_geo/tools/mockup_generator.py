"""
Instagram 목업 생성 도구 - images 폴더 파일 사용 버전
"""
import os
import re
import json
import textwrap
from PIL import Image, ImageDraw
from utils.font_utils import get_korean_font


class InstagramMockupGenerator:
    """Instagram 게시물 목업 생성 클래스"""
    
    def __init__(self, images_folder="./images"):
        self.images_folder = images_folder
    
    def clean_text_for_mockup(self, text):
        """이모지 제거 및 텍스트 정리"""
        if not text:
            return text
        
        # 이모지 패턴 정의
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # 감정 표현
            "\U0001F300-\U0001F5FF"  # 기호 및 픽토그램
            "\U0001F680-\U0001F6FF"  # 교통 및 지도 기호
            "\U0001F1E0-\U0001F1FF"  # 국기
            "\U00002702-\U000027B0"  # 딩벳
            "\U000024C2-\U0001F251"  # 기타 기호
            "]+", flags=re.UNICODE
        )
        
        # 이모지 제거
        cleaned_text = emoji_pattern.sub('', text)
        
        # 추가 정리
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 여러 공백을 하나로
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text
    
    def has_emojis(self, text):
        """텍스트에 이모지가 있는지 확인"""
        if not text:
            return False
            
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]", flags=re.UNICODE
        )
        
        return bool(emoji_pattern.search(text))
    
    
    def create_fallback_image(self):
        """대체 이미지 생성"""
        image = Image.new('RGB', (1080, 1080), color='lightgray')
        draw = ImageDraw.Draw(image)
        text = "KIJUN\n이미지"
        font = get_korean_font(60)
        
        # 텍스트 중앙 배치
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (1080 - text_width) // 2
        y = (1080 - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
        return image
    
    def load_profile_image(self, account_type="official"):
        """프로필 이미지 로드 - images 폴더의 실제 파일 사용"""
        profile_path = os.path.join(self.images_folder, "insta_default_image.jpg")
        
        if os.path.exists(profile_path):
            try:
                profile_image = Image.open(profile_path)
                # RGB 모드로 변환
                if profile_image.mode != 'RGB':
                    profile_image = profile_image.convert('RGB')
                print(f"✅ 실제 프로필 이미지 로드: {profile_path}")
                return profile_image
            except Exception as e:
                print(f"⚠️ 프로필 이미지 로드 실패: {e}")
        
        # 대체 이미지 생성
        print("⚠️ 프로필 이미지를 찾을 수 없어 대체 이미지를 생성합니다.")
        image = Image.new('RGB', (100, 100), color='#0095F6' if account_type == "official" else '#8E8E8E')
        draw = ImageDraw.Draw(image)
        
        text = "K" if account_type == "official" else "U"
        font = get_korean_font(60)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (100 - text_width) // 2
        y = (100 - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
        return image
    
    def load_icon_image(self, icon_type, size=(60, 60)):
        """images 폴더에서 실제 아이콘 파일 로드"""
        icon_filename = f"{icon_type}.png"
        icon_path = os.path.join(self.images_folder, icon_filename)
        
        if os.path.exists(icon_path):
            try:
                icon = Image.open(icon_path)
                # RGBA 모드로 변환하고 크기 조정
                if icon.mode != 'RGBA':
                    icon = icon.convert('RGBA')
                print(f"✅ 실제 {icon_type} 아이콘 로드: {icon_path}")
                return icon.resize(size, Image.Resampling.LANCZOS)
            except Exception as e:
                print(f"⚠️ {icon_type} 아이콘 로드 실패: {e}")
        
        # 대체 아이콘 생성
        print(f"⚠️ {icon_type} 아이콘을 찾을 수 없어 대체 아이콘을 생성합니다.")
        return self.create_icon_image(icon_type, size)
    
    def create_icon_image(self, icon_type, size=(60, 60)):
        """Instagram 아이콘 이미지 생성 (대체용)"""
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # 아이콘별 색상 및 모양 설정
        color = "black"
        center_x, center_y = size[0] // 2, size[1] // 2
        
        if icon_type == "heart":
            # 하트 모양 (단순화된 원형으로 대체)
            draw.ellipse([center_x-15, center_y-15, center_x+15, center_y+15], outline=color, width=3)
        elif icon_type == "comment":
            # 댓글 아이콘 (말풍선)
            draw.ellipse([center_x-18, center_y-15, center_x+18, center_y+15], outline=color, width=3)
            draw.polygon([(center_x-5, center_y+10), (center_x-15, center_y+20), (center_x+5, center_y+15)], outline=color, width=2)
        elif icon_type == "share":
            # 공유 아이콘 (화살표)
            draw.polygon([(center_x-15, center_y), (center_x, center_y-15), (center_x+15, center_y), (center_x, center_y+15)], outline=color, width=3)
        elif icon_type == "bookmark":
            # 북마크 아이콘
            draw.rectangle([center_x-10, center_y-15, center_x+10, center_y+15], outline=color, width=3)
            draw.polygon([(center_x-10, center_y+15), (center_x, center_y+5), (center_x+10, center_y+15)], fill=color)
        
        return image
    
    def load_content_from_json(self, json_filename):
        """JSON 파일에서 캡션과 해시태그 로드"""
        if os.path.exists(json_filename):
            try:
                with open(json_filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # low_score_revisions의 첫 번째 항목에서 데이터 추출
                if 'low_score_revisions' in data and len(data['low_score_revisions']) > 0:
                    content = data['low_score_revisions'][0]
                    caption = content.get('new_caption_v1', '')
                    hashtags = content.get('hashtags', '')
                    
                    print(f"✅ JSON에서 콘텐츠 로드:")
                    print(f"  📝 캡션: {caption[:50]}...")
                    print(f"  🏷️ 해시태그: {hashtags}")
                    
                    return caption, hashtags
                else:
                    print("⚠️ JSON 파일에 low_score_revisions 데이터가 없습니다.")
                    
            except Exception as e:
                print(f"⚠️ JSON 파일 로드 실패: {e}")
        else:
            print(f"⚠️ JSON 파일을 찾을 수 없습니다: {json_filename}")
        
        return None, None
    
    def create_mockup(self, image_path, caption_text, hashtags_text, output_filename, 
                      account_name="kijun_official", account_type="official", json_filename=None):
        """Instagram 목업 생성 메인 함수"""
        try:
            # JSON 파일에서 콘텐츠 로드 (우선순위)
            if json_filename:
                json_caption, json_hashtags = self.load_content_from_json(json_filename)
                if json_caption:
                    caption_text = json_caption
                if json_hashtags:
                    hashtags_text = json_hashtags
            
            # 데이터 유효성 검사
            print(f"🔍 목업 생성 데이터 검증:")
            print(f"  📱 계정 타입: {account_type.upper()}")
            print(f"  👤 계정명: {account_name}")
            print(f"  📝 캡션 길이: {len(caption_text) if caption_text else 0}자")
            print(f"  🏷️ 해시태그 길이: {len(hashtags_text) if hashtags_text else 0}자")
            print(f"  🖼️ 이미지 경로: {image_path}")
            
            # 필수 데이터 확인
            if not caption_text or not caption_text.strip():
                print("⚠️ 캡션이 비어있습니다!")
                caption_text = "KIJUN과 함께하는 특별한 순간"
            
            if not hashtags_text or not hashtags_text.strip():
                print("⚠️ 해시태그가 비어있습니다!")
                hashtags_text = "#KIJUN #패션 #스타일"
            
            # 이모지 제거 및 텍스트 정리
            if self.has_emojis(caption_text):
                print(f"🧹 캡션에서 이모지 제거 중...")
                caption_text = self.clean_text_for_mockup(caption_text)
                print(f"  ✅ 제거 후: {caption_text[:50]}...")
            
            if self.has_emojis(hashtags_text):
                print(f"🧹 해시태그에서 이모지 제거 중...")
                hashtags_text = self.clean_text_for_mockup(hashtags_text)
                print(f"  ✅ 제거 후: {hashtags_text[:50]}...")
            
            print(f"📝 최종 캡션: {caption_text[:50]}...")
            print(f"🏷️ 최종 해시태그: {hashtags_text[:50]}...")
            
            # 메인 이미지 로드
            if image_path and os.path.exists(image_path):
                main_image = Image.open(image_path)
                print(f"✅ 메인 이미지 로드: {image_path}")
            else:
                main_image = self.create_fallback_image()
                print("⚠️ 메인 이미지를 찾을 수 없어 대체 이미지를 생성했습니다.")
            
            # 이미지 크기 조정 (Instagram 규격)
            main_image = main_image.resize((1080, 1080), Image.Resampling.LANCZOS)
            
            # 프로필 이미지 로드 (실제 파일 사용)
            profile_image = self.load_profile_image(account_type)
            
            # 폰트 설정 - 참고 코드 기반으로 크기 조정
            font_bold = get_korean_font(28)
            font_regular = get_korean_font(28)  # 본문도 28로 통일
            font_small = get_korean_font(22)    # 작은 텍스트는 22
            print(f"✅ 한글 폰트 설정 완료")
            
            # 아이콘 로드 (실제 파일 사용)
            icon_size = (60, 60)
            icon_heart = self.load_icon_image("heart", icon_size)
            icon_comment = self.load_icon_image("comment", icon_size)
            icon_share = self.load_icon_image("share", icon_size)
            icon_bookmark = self.load_icon_image("bookmark", icon_size)
            
            # 캔버스 설정 - 푸터 높이 증가
            header_height, footer_height, canvas_width = 120, 650, 1080
            canvas_height = header_height + main_image.height + footer_height
            canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
            draw = ImageDraw.Draw(canvas)
            print(f"✅ 캔버스 설정 완료: {canvas_width}x{canvas_height}")
            
            # 헤더 그리기
            self._draw_header(canvas, draw, profile_image, font_bold, header_height, canvas_width, account_name, account_type)
            print(f"✅ 헤더 그리기 완료")
            
            # 메인 이미지 붙이기
            canvas.paste(main_image, (0, header_height))
            print(f"✅ 메인 이미지 배치 완료")
            
            # 푸터 그리기 - 아이콘 추가
            self._draw_footer(
                canvas, draw, 
                caption_text, hashtags_text,
                font_bold, font_regular, font_small,
                header_height + main_image.height,
                account_name, account_type,
                icon_heart, icon_comment, icon_share, icon_bookmark
            )
            print(f"✅ 푸터 그리기 완료")
            
            # 최종 이미지 저장
            canvas.save(output_filename)
            print(f"✅ Instagram 목업 생성 완료: {output_filename}")
            
            return output_filename
            
        except Exception as e:
            print(f"❌ Instagram 목업 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _draw_header(self, canvas, draw, profile_image, font_bold, header_height, canvas_width, 
                     account_name="kijun_official", account_type="official"):
        """Instagram 헤더 그리기"""
        try:
            # 프로필 이미지
            profile_size = (80, 80)
            profile_image = profile_image.resize(profile_size)
            
            # 원형 마스크 생성
            mask = Image.new('L', profile_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0) + profile_size, fill=255)
            
            # 프로필 이미지 붙이기
            canvas.paste(profile_image, (40, 20), mask=mask)
            
            # 계정명
            draw.text((150, 45), account_name, fill="black", font=font_bold)
            
            # 팔로우 버튼
            if account_type == "official":
                draw.text((canvas_width - 150, 45), "팔로우", fill="#0095F6", font=font_bold)
            else:
                draw.text((canvas_width - 150, 45), "팔로잉", fill="#8E8E8E", font=font_bold)
            
            # 구분선
            draw.line([(0, header_height - 1), (canvas_width, header_height - 1)], fill="#DBDBDB", width=2)
            
        except Exception as e:
            print(f"❌ 헤더 그리기 실패: {e}")
    
    def _draw_footer(self, canvas, draw, caption_text, hashtags_text, 
                     font_bold, font_regular, font_small, start_y,
                     account_name="kijun_official", account_type="official",
                     icon_heart=None, icon_comment=None, icon_share=None, icon_bookmark=None):
        """Instagram 푸터 그리기"""
        try:
            y_cursor = start_y + 30
            
            # 아이콘들 배치 (참고 코드 방식)
            if icon_heart:
                canvas.paste(icon_heart, (40, y_cursor), mask=icon_heart)
            if icon_comment:
                canvas.paste(icon_comment, (120, y_cursor), mask=icon_comment)
            if icon_share:
                canvas.paste(icon_share, (200, y_cursor), mask=icon_share)
            if icon_bookmark:
                canvas.paste(icon_bookmark, (canvas.width - 100, y_cursor), mask=icon_bookmark)
            
            y_cursor += 100  # 아이콘 높이만큼 증가
            
            # 좋아요 (UGC와 공식 계정 차별화)
            if account_type == "ugc":
                like_count = "좋아요 324개"
            else:
                like_count = "좋아요 1,248개"
            
            draw.text((40, y_cursor), like_count, fill="black", font=font_bold)
            y_cursor += 60  # 간격 증가
            
            # 계정명과 캡션 - textlength 사용
            draw.text((40, y_cursor), account_name, fill="black", font=font_bold)
            
            # 정확한 텍스트 길이 계산
            try:
                account_name_width = draw.textlength(f"{account_name} ", font=font_bold)
            except AttributeError:
                # textlength가 없는 경우 대체 방법
                account_name_width = len(account_name) * 15 + 20
            
            # 캡션 텍스트 처리
            y_cursor = self._draw_caption(draw, caption_text, hashtags_text, font_regular, font_small, y_cursor, account_name_width)
            
            # 추가 정보 - 간격 조정
            y_cursor += 20  # 간격 줄임
            if account_type == "ugc":
                comment_text = "댓글 18개 모두 보기"
            else:
                comment_text = "댓글 52개 모두 보기"
            
            draw.text((40, y_cursor), comment_text, fill="#8E8E8E", font=font_small)
            y_cursor += 40
            draw.text((40, y_cursor), "1일 전", fill="#8E8E8E", font=font_small)
            
            return y_cursor
            
        except Exception as e:
            print(f"❌ 푸터 그리기 실패: {e}")
            return start_y + 300
    
    def _draw_caption(self, draw, caption_text, hashtags_text, font_regular, font_small, y_cursor, account_name_width):
        """캡션 텍스트 그리기 - 참고 코드 방식"""
        try:
            # 전체 캡션 텍스트 조합 (참고 코드 방식)
            full_caption_body = f"{caption_text}"
            if hashtags_text:
                full_caption_body += f"\n\n{hashtags_text}"
            
            # 텍스트 래핑 - 참고 코드와 동일하게 50자
            lines = textwrap.wrap(full_caption_body, width=50)
            
            print(f"  📝 캡션 처리: {caption_text[:30]}...")
            print(f"  🏷️ 해시태그 처리: 포함됨")
            print(f"  📄 총 줄 수: {len(lines)}줄")
            
            # 첫 번째 줄은 계정명 옆에, 나머지는 왼쪽 정렬
            if lines:
                # 첫 줄은 계정명 바로 옆에
                draw.text((40 + account_name_width, y_cursor), lines[0], fill="black", font=font_regular)
                y_cursor += 40
                
                # 나머지 줄들
                for line in lines[1:]:
                    draw.text((40, y_cursor), line, fill="black", font=font_regular, spacing=10)
                    y_cursor += 40
            
            return y_cursor
            
        except Exception as e:
            print(f"❌ 캡션 그리기 실패: {e}")
            return y_cursor + 200
