"""
Markdown formatting utilities
"""

from .image_utils import get_absolute_image_path, check_image_exists

def md_heading(text, level=1):
    return f"{'#' * level} {text}"

def md_image(alt_text, path, width=600):
    return f'<img src="{path}" alt="{alt_text}" width="{width}"/>' if path else ""

def md_image_with_fallback(alt_text, path, path2, width=600, fallback_text="이미지 파일을 찾을 수 없습니다"):
    """이미지가 존재하지 않을 경우 대체 텍스트 제공"""
    if path:
        abs_path = get_absolute_image_path(path)
        if check_image_exists(abs_path):
            return f'<img src="{path2}" alt="{alt_text}" width="{width}"/>'
        else:
            return f"*{fallback_text}: {alt_text}*"
    else:
        return f"*{fallback_text}: {alt_text}*"

def md_horizontal_rule():
    return "\n---\n"

def md_blockquote(text):
    lines = text.strip().split("\n")
    quoted_lines = [f"> {line}" if line else ">" for line in lines]
    padding_top = "> &nbsp;"
    padding_bottom = "> &nbsp;"
    return "\n".join([padding_top, *quoted_lines, padding_bottom])

def md_centered_image_with_caption(alt_text, path, path2, width, caption):
    if not path:
        return ""
    abs_path = get_absolute_image_path(path)
    if check_image_exists(abs_path):
        image_md = md_image(alt_text, path2, width)
        return f"| {image_md} |\n| :{'-'*10}: |\n| *{caption}* |"
    else:
        return f"| *이미지 파일을 찾을 수 없습니다: {alt_text}* |\n| :{'-'*10}: |\n| *{caption}* |"
