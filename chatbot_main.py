from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
import os
import re
import json
from datetime import datetime


# -----------------
# 1. FastAPI 앱 생성
# -----------------
app = FastAPI()

# CORS 설정 (React 프론트엔드와 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------
# 2. 파일 및 폴더 설정
# -----------------
# 현재 파일(main.py)의 위치를 기준으로 절대 경로를 만듭니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FOLDER = os.path.join(BASE_DIR, "uploads")
RESULT_FOLDER = os.path.join(BASE_DIR, "result")

# 폴더가 없으면 생성합니다.
os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# JSON 파일 경로
BRANDS_JSON_FILE = os.path.join(RESULT_FOLDER, "brands.json")

# -----------------
# 3. 데이터 모델
# -----------------
class BrandInfo(BaseModel):
    brand_name_ko: Optional[str] = None  # 브랜드 한글 이름
    brand_name_en: Optional[str] = None  # 브랜드 영어 이름
    homepage_url: Optional[str] = None
    instagram_id: Optional[str] = None
    store_address: Optional[str] = None
    
    @validator('brand_name_ko')
    def validate_korean_name(cls, v):
        if v is not None:
            v = v.strip()
            if not re.match(r'^[가-힣\s]+$', v):
                raise ValueError('브랜드 한글명은 한글만 입력 가능합니다.')
            if len(v) < 1:
                raise ValueError('브랜드 한글명을 입력해주세요.')
        return v
    
    @validator('brand_name_en')
    def validate_english_name(cls, v):
        if v is not None:
            v = v.strip()
            if not re.match(r'^[a-zA-Z0-9\s\-&.\'"]+$', v):
                raise ValueError('브랜드 영어명은 영어만 입력 가능합니다.')
            if not re.search(r'[a-zA-Z]', v):
                raise ValueError('브랜드 영어명은 최소 1개 이상의 영문자가 포함되어야 합니다.')
            if len(v) < 1:
                raise ValueError('브랜드 영어명을 입력해주세요.')
        return v
    
    @validator('homepage_url')
    def validate_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            v = 'https://' + v
        return v
    
    @validator('instagram_id')
    def validate_instagram(cls, v):
        if v and v.startswith('@'):
            v = v[1:]  # @ 제거
        if v and not re.match(r'^[a-zA-Z0-9._]+$', v):
            raise ValueError('유효하지 않은 인스타그램 아이디입니다.')
        return v

class ChatbotRequest(BaseModel):
    message: str
    session_id: str
    step: Optional[str] = "brand_name_ko"  # brand_name_ko, brand_name_en, homepage_url, instagram_id, store_address, confirm

class ChatbotResponse(BaseModel):
    message: str
    step: str
    data: Optional[Dict[str, Any]] = None
    is_complete: bool = False

# -----------------
# 4. JSON 파일 처리 함수들
# -----------------
def save_brand_to_json(brand_data: dict) -> dict:
    """브랜드 정보를 JSON 파일에 저장"""
    try:
        # 새로운 브랜드 데이터 생성 (ID는 항상 1로 고정)
        new_brand = {
            "id": 1,
            "brand_name_ko": brand_data["brand_name_ko"],
            "brand_name_en": brand_data["brand_name_en"],
            "homepage_url": brand_data["homepage_url"],
            "instagram_id": brand_data["instagram_id"],
            "store_address": brand_data["store_address"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # JSON 파일에 단일 객체로 저장 (기존 데이터 덮어쓰기)
        with open(BRANDS_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_brand, f, ensure_ascii=False, indent=2)
        
        return new_brand
    
    except Exception as e:
        raise Exception(f"JSON 저장 중 오류: {str(e)}")

def get_brand_from_json() -> dict:
    """저장된 브랜드 정보 조회"""
    try:
        if os.path.exists(BRANDS_JSON_FILE):
            with open(BRANDS_JSON_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        return None


# 세션별 데이터 저장 (실제 환경에서는 Redis나 DB 사용)
chat_sessions: Dict[str, BrandInfo] = {}

# -----------------
# 5. API 엔드포인트 정의
# -----------------

# 루트 경로: 서버가 잘 실행되는지 확인하는 용도
@app.get("/")
async def read_root():
    return {"message": "FastAPI 서버가 정상적으로 실행 중입니다!"}

# 이미지 제공 API
@app.get("/images/{filename:path}")
async def serve_image(filename: str):
    """
    /images/ 경로로 요청된 파일을 'uploads' 폴더에서 찾아 반환합니다.
    """
    file_path = os.path.join(IMAGE_FOLDER, filename)

    if not os.path.exists(file_path):
        return {"error": "Image not found"}, 404

    return FileResponse(file_path)

# -----------------
# 6. 챗봇 API 엔드포인트
# -----------------

@app.post("/chatbot", response_model=ChatbotResponse)
async def chatbot_conversation(request: ChatbotRequest):
    """
    브랜드 정보 수집 챗봇 API
    """
    session_id = request.session_id
    message = request.message.strip()
    
    # 세션 초기화
    if session_id not in chat_sessions:
        chat_sessions[session_id] = BrandInfo()
    
    brand_info = chat_sessions[session_id]
    
    # 단계별 처리
    if request.step == "brand_name_ko":
        return await handle_brand_name_ko(message, session_id, brand_info)
    elif request.step == "brand_name_en":
        return await handle_brand_name_en(message, session_id, brand_info)
    elif request.step == "homepage_url":
        return await handle_homepage_url(message, session_id, brand_info)
    elif request.step == "instagram_id":
        return await handle_instagram_id(message, session_id, brand_info)
    elif request.step == "store_address":
        return await handle_store_address(message, session_id, brand_info)
    elif request.step == "confirm":
        return await handle_confirmation(message, session_id, brand_info)
    else:
        return ChatbotResponse(
            message="알 수 없는 단계입니다. 처음부터 다시 시작해주세요.",
            step="brand_name_ko",
            data=None
        )

async def handle_brand_name_ko(message: str, session_id: str, brand_info: BrandInfo) -> ChatbotResponse:
    """브랜드 한글명 처리"""
    if len(message) < 1:
        return ChatbotResponse(
            message="브랜드 한글명을 입력해주세요. (최소 1글자 이상)",
            step="brand_name_ko"
        )
    
    # 한글만 허용 (공백 포함)
    if not re.match(r'^[가-힣\s]+$', message):
        return ChatbotResponse(
            message="브랜드 한글명은 한글만 입력 가능합니다. 다시 입력해주세요.\n\n예시: 스타벅스, 투썸 플레이스",
            step="brand_name_ko"
        )
    
    # 공백 제거 후 길이 확인
    if len(message.strip()) < 1:
        return ChatbotResponse(
            message="브랜드 한글명을 입력해주세요. (공백만으로는 입력할 수 없습니다)",
            step="brand_name_ko"
        )
    
    brand_info.brand_name_ko = message.strip()
    chat_sessions[session_id] = brand_info
    
    return ChatbotResponse(
        message=f"브랜드 한글명 '{message.strip()}'가 등록되었습니다.\n\n이제 브랜드 영어명을 입력해주세요.",
        step="brand_name_en",
        data={"brand_name_ko": message.strip()}
    )

async def handle_brand_name_en(message: str, session_id: str, brand_info: BrandInfo) -> ChatbotResponse:
    """브랜드 영어명 처리"""
    if len(message) < 1:
        return ChatbotResponse(
            message="브랜드 영어명을 입력해주세요. (최소 1글자 이상)",
            step="brand_name_en"
        )
    
    # 영어, 숫자, 공백, 특수문자(-, &, ., ', ") 허용
    if not re.match(r'^[a-zA-Z0-9\s\-&.\'"]+$', message):
        return ChatbotResponse(
            message="브랜드 영어명은 영어만 입력 가능합니다. 다시 입력해주세요.\n\n예시: Starbucks, McDonald's, H&M",
            step="brand_name_en"
        )
    
    # 공백 제거 후 길이 확인
    if len(message.strip()) < 1:
        return ChatbotResponse(
            message="브랜드 영어명을 입력해주세요. (공백만으로는 입력할 수 없습니다)",
            step="brand_name_en"
        )
    
    # 최소 1개 이상의 영문자가 포함되어야 함
    if not re.search(r'[a-zA-Z]', message):
        return ChatbotResponse(
            message="브랜드 영어명은 최소 1개 이상의 영문자가 포함되어야 합니다.",
            step="brand_name_en"
        )
    
    brand_info.brand_name_en = message.strip()
    chat_sessions[session_id] = brand_info
    
    return ChatbotResponse(
        message=f"브랜드 영어명 '{message.strip()}'가 등록되었습니다.\n\n이제 홈페이지 URL을 입력해주세요. (예: www.example.com 또는 https://www.example.com)",
        step="homepage_url",
        data={"brand_name_en": message.strip()}
    )

async def handle_homepage_url(message: str, session_id: str, brand_info: BrandInfo) -> ChatbotResponse:
    """홈페이지 URL 처리"""
    try:
        # URL 검증 및 정규화
        if not message.startswith(('http://', 'https://')):
            message = 'https://' + message
        
        # 기본적인 URL 형식 검증
        if not re.match(r'https?://[^\s]+\.[^\s]+', message):
            return ChatbotResponse(
                message="올바른 URL 형식을 입력해주세요. (예: www.example.com)",
                step="homepage_url"
            )
        
        brand_info.homepage_url = message
        chat_sessions[session_id] = brand_info
        
        return ChatbotResponse(
            message=f"홈페이지 URL '{message}'가 등록되었습니다.\n\n이제 인스타그램 아이디를 입력해주세요. (예: @username 또는 username)",
            step="instagram_id",
            data={"homepage_url": message}
        )
    except Exception as e:
        return ChatbotResponse(
            message="URL 형식이 올바르지 않습니다. 다시 입력해주세요.",
            step="homepage_url"
        )

async def handle_instagram_id(message: str, session_id: str, brand_info: BrandInfo) -> ChatbotResponse:
    """인스타그램 아이디 처리"""
    try:
        # @ 제거
        if message.startswith('@'):
            message = message[1:]
        
        # 인스타그램 아이디 검증 (영문, 숫자, 점, 언더스코어만 허용)
        if not re.match(r'^[a-zA-Z0-9._]+$', message):
            return ChatbotResponse(
                message="올바른 인스타그램 아이디를 입력해주세요. (영문, 숫자, 점, 언더스코어만 사용 가능)",
                step="instagram_id"
            )
        
        brand_info.instagram_id = message
        chat_sessions[session_id] = brand_info
        
        return ChatbotResponse(
            message=f"인스타그램 아이디 '@{message}'가 등록되었습니다.\n\n마지막으로 매장 주소를 입력해주세요.",
            step="store_address",
            data={"instagram_id": f"@{message}"}
        )
    except Exception as e:
        return ChatbotResponse(
            message="인스타그램 아이디 형식이 올바르지 않습니다. 다시 입력해주세요.",
            step="instagram_id"
        )

async def handle_store_address(message: str, session_id: str, brand_info: BrandInfo) -> ChatbotResponse:
    """매장 주소 처리"""
    if len(message) < 5:
        return ChatbotResponse(
            message="매장 주소를 정확히 입력해주세요. (최소 5글자 이상)",
            step="store_address"
        )
    
    brand_info.store_address = message
    chat_sessions[session_id] = brand_info
    
    # 모든 정보 수집 완료, 확인 단계로
    summary = f"""
✅ 입력하신 정보를 확인해주세요:

🏢 브랜드 한글명: {brand_info.brand_name_ko}
🏢 브랜드 영어명: {brand_info.brand_name_en}
🌐 홈페이지: {brand_info.homepage_url}
📱 인스타그램: @{brand_info.instagram_id}
📍 매장 주소: {brand_info.store_address}

위 정보가 맞나요? 
- 맞다면 '확인' 또는 '네'를 입력해주세요.
- 틀렸다면 '수정' 또는 '아니오'를 입력해주세요.
"""
    
    return ChatbotResponse(
        message=summary,
        step="confirm",
        data={
            "brand_name_ko": brand_info.brand_name_ko,
            "brand_name_en": brand_info.brand_name_en,
            "homepage_url": brand_info.homepage_url,
            "instagram_id": f"@{brand_info.instagram_id}",
            "store_address": brand_info.store_address
        }
    )

async def handle_confirmation(message: str, session_id: str, brand_info: BrandInfo) -> ChatbotResponse:
    """최종 확인 처리"""
    message_lower = message.lower()
    
    if message_lower in ['확인', '네', '맞습니다', 'yes', 'y', '맞음', '정확']:
        # JSON 파일에 저장
        final_data = {
            "brand_name_ko": brand_info.brand_name_ko,
            "brand_name_en": brand_info.brand_name_en,
            "homepage_url": brand_info.homepage_url,
            "instagram_id": brand_info.instagram_id,
            "store_address": brand_info.store_address
        }
        
        try:
            saved_brand = save_brand_to_json(final_data)
            
            # 세션 정리
            if session_id in chat_sessions:
                del chat_sessions[session_id]
            
            return ChatbotResponse(
                message=f"✅ 브랜드 정보가 성공적으로 등록되었습니다!",
                step="complete",
                data=final_data,
                is_complete=True
            )
        except Exception as error:
            return ChatbotResponse(
                message=f"❌ 저장 중 오류가 발생했습니다:\n\n{str(error)}\n\n다시 시도해주세요.",
                step="confirm"
            )
    
    elif message_lower in ['수정', '아니오', '틀렸습니다', 'no', 'n', '다시']:
        # 처음부터 다시 시작
        if session_id in chat_sessions:
            del chat_sessions[session_id]
        
        return ChatbotResponse(
            message="정보를 다시 입력받겠습니다.\n\n브랜드 한글명부터 다시 입력해주세요.",
            step="brand_name_ko",
            data=None
        )
    
    else:
        return ChatbotResponse(
            message="'확인' 또는 '수정' 중 하나를 선택해주세요.\n\n- 정보가 맞다면: '확인' 또는 '네'\n- 다시 입력하려면: '수정' 또는 '아니오'",
            step="confirm"
        )

@app.get("/chatbot/start")
async def start_chatbot():
    """챗봇 시작 메시지"""
    return ChatbotResponse(
        message="안녕하세요! 브랜드 등록을 도와드리겠습니다. 😊\n\n먼저 브랜드 한글명을 입력해주세요.",
        step="brand_name_ko",
        data=None
    )

@app.get("/chatbot/sessions")
async def get_active_sessions():
    """활성 세션 목록 (개발용)"""
    return {
        "active_sessions": len(chat_sessions),
        "sessions": list(chat_sessions.keys())
    }

@app.get("/brands")
async def get_brands():
    """저장된 브랜드 정보 조회"""
    try:
        brand = get_brand_from_json()
        if brand:
            return {
                "brand": brand,
                "message": "JSON 파일에서 조회된 브랜드 정보",
                "source": "json"
            }
        else:
            return {
                "brand": None,
                "message": "저장된 브랜드 정보가 없습니다",
                "source": "none"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"브랜드 정보 조회 중 오류: {str(e)}")

@app.get("/brands/{brand_id}")
async def get_brand_by_id(brand_id: int):
    """특정 브랜드 정보 조회 (ID는 항상 1)"""
    try:
        if brand_id != 1:
            raise HTTPException(status_code=404, detail="브랜드 ID는 1만 사용 가능합니다")
        
        brand = get_brand_from_json()
        if not brand:
            raise HTTPException(status_code=404, detail="저장된 브랜드 정보가 없습니다")
        return brand
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"브랜드 정보 조회 중 오류: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)