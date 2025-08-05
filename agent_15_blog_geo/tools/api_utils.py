"""
API Utilities for Blog GEO Analysis

Handles OpenAI API calls with retry logic and JSON repair.
"""

import json
import time
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI


# Configuration
MAX_RETRIES = 10
RETRY_DELAY = 10


def repair_json_with_llm(
    client: OpenAI,
    broken_json: str,
    model: str = "gpt-4o-mini"
) -> dict:
    """
    Use LLM to repair broken JSON string
    
    Args:
        client: OpenAI client
        broken_json: Malformed JSON string
        model: Model to use for repair
        
    Returns:
        Repaired JSON as dictionary
        
    Raises:
        Exception if repair fails
    """
    print("  - 잘못된 JSON 형식 감지됨. AI로 자동 복구 시도...")
    
    repair_prompt = (
        "The following string is not a valid JSON. Please fix it and return ONLY "
        "the corrected and valid JSON object. Do not add any text before or after "
        f"the JSON object. Broken JSON: {broken_json}"
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a JSON repair expert."},
                {"role": "user", "content": repair_prompt}
            ],
            temperature=0
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"  - [오류] JSON 복구 실패: {e}")
        raise e


def call_openai_api(
    client: OpenAI,
    messages: List[Dict[str, Any]],
    model: str = "gpt-4o-mini",
    max_tokens: int = 2048,
    temperature: float = 0.3
) -> dict:
    """
    Call OpenAI API with JSON response format
    
    Args:
        client: OpenAI client
        messages: Chat messages
        model: Model to use
        max_tokens: Maximum tokens in response
        temperature: Temperature for generation
        
    Returns:
        Parsed JSON response
        
    Raises:
        ConnectionError if client not initialized
    """
    if not client:
        raise ConnectionError("OpenAI 클라이언트가 초기화되지 않았습니다.")
    
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    original_content = response.choices[0].message.content
    
    try:
        return json.loads(original_content)
    except json.JSONDecodeError:
        return repair_json_with_llm(client, original_content, model)


def call_api_with_retry(
    client: OpenAI,
    messages: List[Dict[str, Any]],
    model: str = "gpt-4o-mini",
    max_tokens: int = 2048,
    temperature: float = 0.3,
    max_retries: int = MAX_RETRIES,
    retry_delay: int = RETRY_DELAY
) -> Dict[str, Any]:
    """
    Call API with retry logic for rate limits
    
    Args:
        client: OpenAI client
        messages: Chat messages
        model: Model to use
        max_tokens: Maximum tokens
        temperature: Temperature setting
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        API response as dictionary
        
    Raises:
        Exception if all retries fail
    """
    for attempt in range(max_retries):
        try:
            return call_openai_api(
                client=client,
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
        except Exception as e:
            error_message = str(e)
            
            if '429' in error_message or 'Rate limit' in error_message:
                if attempt < max_retries - 1:
                    print(f"  - [경고] Rate limit 발생. {retry_delay}초 후 재시도... (시도 {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    print(f"  - [오류] 최대 재시도 횟수({max_retries}) 초과. 중단합니다.")
                    raise e
            else:
                raise e
    
    raise Exception("API 호출이 반복적으로 실패했습니다.")


def generate_dalle_image(
    client: OpenAI,
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard"
) -> Optional[str]:
    """
    Generate image using DALL-E 3
    
    Args:
        client: OpenAI client
        prompt: Image generation prompt
        size: Image size
        quality: Image quality
        
    Returns:
        Base64 encoded image or None if failed
    """
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size=size,
            quality=quality,
            response_format="b64_json"
        )
        
        return response.data[0].b64_json
        
    except Exception as e:
        print(f"    [오류] DALL-E 이미지 생성 실패: {e}")
        return None


def create_chat_completion(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 1024,
    temperature: float = 0.7
) -> Optional[str]:
    """
    Create a simple chat completion (non-JSON response)
    
    Args:
        client: OpenAI client
        system_prompt: System message
        user_prompt: User message
        model: Model to use
        max_tokens: Maximum tokens
        temperature: Temperature setting
        
    Returns:
        Generated text or None if failed
    """
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"  - [오류] Chat completion 생성 실패: {e}")
        return None