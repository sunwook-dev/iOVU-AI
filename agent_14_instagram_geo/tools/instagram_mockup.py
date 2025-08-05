"""
Instagram 목업 생성 함수
"""

import os
import json
import textwrap
from PIL import Image, ImageDraw
from utils.font_utils import get_korean_font


def load_or_create_icon(images_folder, icon_name, size=(50, 50)):
    """아이콘 로드 또는 생성"""
    icon_path = os.path.join(images_folder, f"{icon_name}.png")
    try:
        if os.path.exists(icon_path):
            icon = Image.open(icon_path).convert("RGBA").resize(size)
            print(f"✅ 아이콘 로드: {icon_name}.png")
            return icon
        else:
            # 기본 아이콘 생성
            icon = Image.new("RGBA", size, (128, 128, 128, 180))
            draw = ImageDraw.Draw(icon)
            draw.ellipse(
                [10, 10, size[0] - 10, size[1] - 10], fill=(200, 200, 200, 200)
            )
            print(f"⚠️ {icon_name}.png 없음 - 기본 아이콘 생성")
            return icon
    except Exception as e:
        print(f"⚠️ {icon_name} 아이콘 로드 실패: {e}")
        icon = Image.new("RGBA", size, (128, 128, 128, 180))
        draw = ImageDraw.Draw(icon)
        draw.ellipse([10, 10, size[0] - 10, size[1] - 10], fill=(200, 200, 200, 200))
        return icon


def load_or_create_profile_image(images_folder):
    """프로필 이미지 로드 (insta_default_image.jpg 사용)"""
    profile_path = os.path.join(images_folder, "insta_default_image.jpg")
    try:
        if os.path.exists(profile_path):
            profile_image = Image.open(profile_path)
            print(f"✅ 프로필 이미지 로드: insta_default_image.jpg")
            return profile_image
        else:
            # 기본 프로필 이미지 생성
            profile_image = Image.new("RGB", (80, 80), (150, 150, 150))
            draw = ImageDraw.Draw(profile_image)
            draw.text((40, 40), "K", fill="white", anchor="mm")
            print(f"⚠️ insta_default_image.jpg 없음 - 기본 프로필 생성")
            return profile_image
    except Exception as e:
        print(f"⚠️ 프로필 이미지 로드 실패: {e}")
        profile_image = Image.new("RGB", (80, 80), (150, 150, 150))
        draw = ImageDraw.Draw(profile_image)
        draw.text((40, 40), "K", fill="white", anchor="mm")
        return profile_image


def create_instagram_mockup(image_path, content_filename):
    """3단계: Instagram 게시물 목업 생성"""
    print(f"\n📱 3단계: Instagram 목업 생성 시작")

    try:
        # 이미지 경로 설정
        images_folder = "D:\\edu_data\\AI_Prompt\\workspace\\final_project\\modular_agents\\agent_14_instagram_geo\\images"

        # JSON 데이터 로드
        with open(content_filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        caption_data = data["low_score_revisions"][0]
        caption_text = caption_data["new_caption_v1"]
        hashtags_text = caption_data["hashtags"]

        print(f"📝 캡션: {caption_text[:50]}...")
        print(f"🏷️ 해시태그: {hashtags_text[:50]}...")

        # 메인 이미지 로드
        if os.path.exists(image_path):
            main_image = Image.open(image_path)
            print(f"✅ 메인 이미지 로드: {image_path}")
        else:
            # 대체 이미지 생성
            main_image = Image.new("RGB", (1024, 1024), (240, 240, 240))
            draw = ImageDraw.Draw(main_image)
            draw.text(
                (400, 500), "KIJUN\nGenerated Image", fill=(100, 100, 100), anchor="mm"
            )
            print("⚠️ 메인 이미지를 찾을 수 없어 대체 이미지를 생성했습니다.")

        # 프로필 이미지 로드
        profile_image = load_or_create_profile_image(images_folder)

        # 폰트 설정
        font_bold = get_korean_font(28)
        font_regular = get_korean_font(24)
        font_small = get_korean_font(20)

        # 아이콘 로드
        icon_size = (50, 50)
        icon_heart = load_or_create_icon(images_folder, "heart", icon_size)
        icon_comment = load_or_create_icon(images_folder, "comment", icon_size)
        icon_share = load_or_create_icon(images_folder, "share", icon_size)
        icon_bookmark = load_or_create_icon(images_folder, "bookmark", icon_size)

        # 캔버스 설정
        width, height = main_image.size
        if width != 1080:
            new_height = int(height * (1080 / width))
            main_image = main_image.resize((1080, new_height))

        header_height, footer_height, canvas_width = 120, 800, 1080
        canvas_height = header_height + main_image.height + footer_height
        canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
        draw = ImageDraw.Draw(canvas)

        # 헤더 그리기
        profile_size = (80, 80)
        profile_image = profile_image.resize(profile_size)
        mask = Image.new("L", profile_size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + profile_size, fill=255)
        canvas.paste(profile_image, (40, 20), mask=mask)

        draw.text((150, 45), "kijun_official", fill="black", font=font_bold)
        draw.text((canvas_width - 150, 45), "팔로우", fill="#0095F6", font=font_bold)
        draw.line(
            [(0, header_height - 1), (canvas_width, header_height - 1)],
            fill="#DBDBDB",
            width=2,
        )

        # 메인 이미지
        canvas.paste(main_image, (0, header_height))

        # 푸터
        y_cursor = header_height + main_image.height + 30

        # 아이콘들
        canvas.paste(icon_heart, (40, y_cursor), mask=icon_heart)
        canvas.paste(icon_comment, (120, y_cursor), mask=icon_comment)
        canvas.paste(icon_share, (200, y_cursor), mask=icon_share)
        canvas.paste(icon_bookmark, (canvas_width - 120, y_cursor), mask=icon_bookmark)
        y_cursor += 80

        # 좋아요
        draw.text((40, y_cursor), "좋아요 1,248개", fill="black", font=font_bold)
        y_cursor += 50

        # 계정명과 캡션
        draw.text((40, y_cursor), "kijun_official ", fill="black", font=font_bold)

        # 캡션 텍스트 처리
        caption_lines = []
        wrap_width = 40

        # 캡션을 줄바꿈 기준으로 분할
        caption_parts = caption_text.split("\n")
        for part in caption_parts:
            if len(part) > wrap_width:
                wrapped = textwrap.wrap(part, width=wrap_width)
                caption_lines.extend(wrapped)
            else:
                caption_lines.append(part)

        # 해시태그 추가
        if hashtags_text:
            caption_lines.append("")
            hashtag_lines = textwrap.wrap(hashtags_text, width=wrap_width)
            caption_lines.extend(hashtag_lines)

        # 캡션 그리기 (최대 8줄)
        account_name_width = 180

        for i, line in enumerate(caption_lines[:8]):
            if i == 0:
                # 첫 줄은 계정명 옆에
                draw.text(
                    (40 + account_name_width, y_cursor),
                    line,
                    fill="black",
                    font=font_regular,
                )
            else:
                # 나머지 줄은 왼쪽 정렬
                y_cursor += 35
                draw.text((40, y_cursor), line, fill="black", font=font_regular)

        # 더 많은 텍스트가 있으면 "더 보기" 표시
        if len(caption_lines) > 8:
            y_cursor += 35
            draw.text((40, y_cursor), "...더 보기", fill="#8E8E8E", font=font_small)

        y_cursor += 50
        draw.text(
            (40, y_cursor), "댓글 52개 모두 보기", fill="#8E8E8E", font=font_small
        )
        y_cursor += 40
        draw.text((40, y_cursor), "1일 전", fill="#8E8E8E", font=font_small)

        # 최종 이미지 저장 - modular_agents/outputs에 저장
        from pathlib import Path
        current_file = Path(__file__)  # agent_14_instagram_geo/tools/instagram_mockup.py
        modular_agents_dir = current_file.parent.parent.parent  # Go up to modular_agents
        output_dir = modular_agents_dir / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        base_filename = os.path.basename(content_filename).replace(
            "_generated_content.json", ""
        )
        output_path = output_dir / f"{base_filename}_instagram_mockup.jpg"
        canvas.save(str(output_path))
        print(f"✅ 3단계 완료 - Instagram 목업: {output_path}")

        return str(output_path)

    except Exception as e:
        print(f"❌ Instagram 목업 생성 실패: {e}")
        import traceback

        traceback.print_exc()
        return False
