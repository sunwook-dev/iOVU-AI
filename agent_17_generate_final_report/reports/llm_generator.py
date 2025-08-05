"""
LLM text generation utilities
"""

import os
from openai import OpenAI
from utils.config import CONFIG

_SYSTEM_PROMPT = """
당신은 전문 디지털 마케팅 분석가입니다. 
주어진 데이터를 바탕으로 비즈니스 보고서의 각 섹션을 작성하는 임무를 맡았습니다.
'GEO'는 'Generative Engine Optimization' 즉, '생성형 엔진 최적화'를 의미합니다.
보고서는 한국어로, 전문적이고 간결하며 데이터에 기반한 어조로 작성해야 합니다.
결과는 반드시 마크다운 형식으로만 출력해 주세요. 제목(헤딩)은 제외하고 본문 내용만 작성하세요.
"""

def generate_text_with_llm(prompt, context_data_str):
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model=CONFIG["llm_model"],
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"{prompt}\n\n컨텍스트 데이터:\n{context_data_str}"}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM 생성 오류: {e}")
        return f"LLM 분석 결과를 생성할 수 없습니다. 오류: {e}"
