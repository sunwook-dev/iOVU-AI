"""
Image Utility Functions

Handles image composition and manipulation.
"""

import os
from typing import Optional
from PIL import Image, ImageDraw, ImageFont


def wrap_text_by_pixel(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    """
    Wrap text based on pixel width

    Args:
        text: Text to wrap
        font: Font object
        max_width: Maximum width in pixels

    Returns:
        List of wrapped lines
    """
    lines = []
    words = text.split(" ")
    current_line = ""

    for word in words:
        # Test line with added word
        test_line = f"{current_line} {word}".strip()
        if font.getbbox(test_line)[2] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)  # Add last line
    return lines


def create_blog_image(
    title: str,
    body_text: str,
    image_path: str,
    output_filename: str,
    output_dir: str = "../outputs",
) -> Optional[str]:
    """
    Create composed blog image with title, image, and body text

    Args:
        title: Blog post title
        body_text: Blog post body
        image_path: Path to DALL-E generated image
        output_filename: Output filename
        output_dir: Output directory

    Returns:
        Path to generated image or None if failed
    """
    try:
        from pathlib import Path

        if not os.path.exists(image_path):
            print(f"  - [오류] 이미지 파일을 찾을 수 없습니다: '{image_path}'")
            return None

        # Load base image
        base_img = Image.open(image_path).convert("RGB")
        img_width, img_height = base_img.size

        # Font settings
        margin = 80

        # Try to use system fonts
        title_font_path = None
        body_font_path = None

        # Common font paths
        font_paths = [
            # Korean fonts
            "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            # Fallback to common fonts
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            # Windows fonts
            "C:/Windows/Fonts/malgun.ttf",
            "C:/Windows/Fonts/malgunbd.ttf",
        ]

        # Find available fonts
        for path in font_paths:
            if os.path.exists(path):
                if "Bold" in path or "bd" in path:
                    title_font_path = title_font_path or path
                else:
                    body_font_path = body_font_path or path

        # Use default if no fonts found
        if not title_font_path or not body_font_path:
            try:
                title_font = ImageFont.load_default()
                body_font = ImageFont.load_default()
                initial_title_size = 24
                body_font_size = 16
            except:
                print("  - [오류] 시스템 폰트 로드 실패. PIL 기본 폰트 사용.")
                title_font = ImageFont.load_default()
                body_font = ImageFont.load_default()
                initial_title_size = 24
                body_font_size = 16
        else:
            initial_title_size = 42
            body_font_size = 22

            # Dynamic title font size
            title_font_size = initial_title_size
            title_font = ImageFont.truetype(title_font_path, title_font_size)
            while (
                title_font.getbbox(title)[2] > img_width - 2 * margin
                and title_font_size > 20
            ):
                title_font_size -= 2
                title_font = ImageFont.truetype(title_font_path, title_font_size)

            body_font = ImageFont.truetype(body_font_path, body_font_size)

        # Text layout calculations
        header_margin_top_bottom = 50
        body_margin_top_bottom = 50
        line_spacing = 12
        paragraph_spacing = 25

        # Title height
        title_bbox = title_font.getbbox(title)
        title_height = title_bbox[3] - title_bbox[1]
        header_height = title_height + 2 * header_margin_top_bottom

        # Body text height
        max_text_width = img_width - (2 * margin)
        body_paragraphs = body_text.strip().split("\n\n")
        total_body_height = 0
        wrapped_paragraphs = []

        for para in body_paragraphs:
            lines = wrap_text_by_pixel(para, body_font, max_text_width)
            if not lines:
                continue
            wrapped_paragraphs.append(lines)

            para_height = (
                sum(
                    [
                        body_font.getbbox(line)[3] - body_font.getbbox(line)[1]
                        for line in lines
                    ]
                )
                + len(lines) * line_spacing
            )
            total_body_height += para_height

        total_body_height += (len(wrapped_paragraphs) - 1) * paragraph_spacing
        body_height = total_body_height + 2 * body_margin_top_bottom

        # Create final image
        total_height = header_height + img_height + body_height
        new_img = Image.new("RGB", (img_width, total_height), color=(255, 255, 255))
        draw = ImageDraw.Draw(new_img)

        # Draw title (centered)
        title_width = title_font.getbbox(title)[2]
        title_x = (img_width - title_width) / 2
        title_y = header_margin_top_bottom
        draw.text((title_x, title_y), title, fill=(0, 0, 0), font=title_font)

        # Paste DALL-E image
        new_img.paste(base_img, (0, header_height))

        # Draw body text (centered)
        y_text = header_height + img_height + body_margin_top_bottom
        for para_lines in wrapped_paragraphs:
            for line in para_lines:
                line_width = body_font.getbbox(line)[2]
                text_x = (img_width - line_width) / 2
                draw.text((text_x, y_text), line, fill=(50, 50, 50), font=body_font)
                y_text += (
                    body_font.getbbox(line)[3] - body_font.getbbox(line)[1]
                ) + line_spacing
            y_text += paragraph_spacing

        # Save final image
        # Always save to modular_agents/output regardless of caller location
        from pathlib import Path

        # Get modular_agents directory
        current_file = Path(__file__)  # agent_15_blog_geo/utils/image_utils.py
        modular_agents_dir = current_file.parent.parent.parent  # Go up to modular_agents
        output_path = modular_agents_dir / "outputs"
        output_path.mkdir(parents=True, exist_ok=True)
        # Ensure output_filename is just a filename, not a relative path
        output_filename_clean = Path(output_filename).name
        final_path = output_path / output_filename_clean
        new_img.save(str(final_path), quality=95)
        print(f"  - 블로그 이미지 생성 완료: {final_path}")
        return str(final_path)

    except Exception as e:
        print(f"  - [오류] 블로그 이미지 생성 실패: {e}")
        import traceback

        traceback.print_exc()
        return None
