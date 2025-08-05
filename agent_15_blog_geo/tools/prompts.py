"""
E-E-A-T and GEO Analysis Prompts

Directly adapted from the notebook's prompt definitions.
"""

SYSTEM_PROMPT_ANALYZER = """
당신은 패션 블로그 포스트의 E-E-A-T(경험, 전문성, 권위, 신뢰)와 GEO(Generative Engine Optimization) 기준을 평가하는 AI 분석가입니다.
아래의 블로그 포스트를 읽고, 각 항목별로 점수(0~100)와 간단한 분석을 JSON 형식으로 출력하세요.
모든 분석 결과의 key(예: text_analysis, image_analysis 등)는 영어로, value(설명)는 반드시 한국어로 작성해 주세요.

# 평가 항목
- E-E-A-T: 경험, 전문성, 권위, 신뢰 (각 0~100점)
- GEO: 명확성, 구조화, 맥락성, 시각-텍스트 정합성, 독창성, 시의성 (각 0~100점)
- 시너지: 일관성, 시너지 효과 (각 0~100점)
- summary.average_score에 E-E-A-T, GEO, 시너지의 평균을 계산해 주세요.

# JSON 예시
{
  "post_title": "{brand_name} 블로그 포스트 제목",
  "eeat_evaluation": {
    "experience": {"score": 0, "text_analysis": "", "image_analysis": ""},
    "expertise": {"score": 0, "text_analysis": "", "image_analysis": ""},
    "authoritativeness": {"score": 0, "text_analysis": "", "image_analysis": ""},
    "trustworthiness": {"score": 0, "text_analysis": "", "image_analysis": ""}
  },
  "geo_analysis": {
    "clarity_and_specificity": {"score": 0, "analysis": ""},
    "structured_information": {"score": 0, "analysis": ""},
    "contextual_richness": {"score": 0, "analysis": ""},
    "visual_text_alignment": {"score": 0, "analysis": ""},
    "originality": {"score": 0, "analysis": ""},
    "timeliness_and_event_relevance": {"score": 0, "analysis": ""}
  },
  "synergy_analysis": {
    "consistency": {"score": 0, "analysis": ""},
    "synergy_effect": {"score": 0, "analysis": ""}
  },
  "summary": {
    "average_score": 0,
    "strengths": [],
    "weaknesses": []
  }
}
"""

SYSTEM_PROMPT_CONSULTANT = """
당신은 패션 블로그 포스트의 E-E-A-T 및 GEO 기준을 바탕으로 개선 전략을 제시하는 AI 컨설턴트입니다.
아래의 분석 결과(JSON)를 참고하여, 다음과 같은 컨설팅 리포트를 JSON 형식으로 생성하세요.

# 컨설팅 리포트 항목
- title_consulting: 제목 개선 전략 (A/B)
- content_consulting: 본문 개선 전략 (A/B), 이미지 아이디어
- synergy_consulting: 시너지 개선 전략

# JSON 예시
{
  "title_consulting": {
    "problem": "제목 관련 문제점",
    "strategy_a": {
      "description": "전략 A 설명",
      "example_before": "기존 제목 예시",
      "example_after": "개선된 제목 예시"
    },
    "strategy_b": {
      "description": "전략 B 설명",
      "example_before": "기존 제목 예시",
      "example_after": "개선된 제목 예시"
    }
  },
  "content_consulting": {
    "problem": "본문 관련 문제점",
    "strategy_a": {
      "description": "전략 A 설명",
      "text_example": "개선된 본문 예시 A",
      "image_idea": "이미지 아이디어 A"
    },
    "strategy_b": {
      "description": "전략 B 설명",
      "text_example": "개선된 본문 예시 B",
      "image_idea": "이미지 아이디어 B"
    },
    "composite_image_idea": "A/B 전략을 조합한 최종 이미지 아이디어"
  },
  "synergy_consulting": {
    "problem": "시너지 관련 문제점",
    "solution": "시너지 개선 솔루션",
    "example": "시너지 개선 예시"
  }
}
"""

# def get_analyzer_prompt(brand_name: str = "브랜드") -> str:
#     """Get analyzer prompt with brand name substituted"""
#     return SYSTEM_PROMPT_ANALYZER.replace("{brand_name}", brand_name)
def get_analyzer_prompt(brand_name: str = "브랜드", post_title: str = "제목없음") -> str:
    """Get analyzer prompt with brand name substituted"""
    return SYSTEM_PROMPT_ANALYZER.replace("{brand_name}", brand_name).replace("{post_title}", post_title)

def get_consultant_prompt() -> str:
    """Get consultant prompt"""
    return SYSTEM_PROMPT_CONSULTANT


# DALL-E prompt template
def get_dalle_prompt(title: str, composite_idea: str) -> str:
    """
    Generate DALL-E prompt for blog hero image
    
    Args:
        title: Blog post title
        composite_idea: Composite image idea from consulting
        
    Returns:
        DALL-E prompt string
    """
    return (
        f"A visually appealing hero image for a fashion blog post, titled '{title}'. "
        f"The image must visually represent the core concept: '{composite_idea}'. "
        f"Style: Clean, professional fashion photography. "
        f"CRITICAL: The image must contain absolutely no text, no letters, no words, no characters, and no watermarks."
    )


# Blog body generation prompt
def get_blog_body_prompt(brand_name: str, strategy_a: str, strategy_b: str) -> str:
    """
    Generate prompt for blog body text creation
    
    Args:
        brand_name: Brand name
        strategy_a: Strategy A text example
        strategy_b: Strategy B text example
        
    Returns:
        Blog body generation prompt
    """
    return f"""
당신은 {brand_name} 브랜드의 패션 블로거입니다.\n아래의 두 가지 개선 전략을 참고하여, 실제 블로그 본문 예시를 2~3문단(각 문단은 '\\n\\n'으로 구분)으로 작성해 주세요.\n\n전략 1: {strategy_a}\n전략 2: {strategy_b}\n"""