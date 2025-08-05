# Agent 06 Web Refiner 최적화 계획

## 현재 중복 기능
1. **메타데이터 추출** - Agent 10도 엔티티/제품 정보 추출
2. **제품 정보 파싱** - Agent 10의 엔티티 추출과 중복
3. **구조화된 데이터 저장** - Agent 10이 더 상세하게 처리

## 제안하는 Agent 06 축소 버전

### 유지할 핵심 기능
1. **HTML 정리** (html_cleaner.py)
   - 노이즈 제거
   - 메인 콘텐츠 추출

2. **텍스트 추출** (text_extractor.py)
   - Trafilatura 사용
   - 순수 텍스트만 추출

3. **텍스트 정리** (text_cleaner.py)
   - 개인정보 제거
   - 텍스트 정규화

4. **기본 품질 평가** (quality_evaluator.py 간소화)
   - 텍스트 길이 체크
   - 기본 품질 점수만

### 제거할 기능
1. ~~metadata_extractor.py~~ → Agent 10이 처리
2. ~~product_parser.py~~ → Agent 10이 처리
3. ~~entities 필드 저장~~ → Agent 10이 처리
4. ~~복잡한 품질 평가~~ → 간소화

### 수정된 프로세스
```python
def _process_single_item(self, connection, data):
    # 1. HTML 정리
    cleaned_html = self.html_cleaner.clean(data['html_content'])
    
    # 2. 텍스트 추출
    extraction_result = self.text_extractor.extract_text(cleaned_html)
    
    # 3. 텍스트 정리
    cleaned_text = self.text_cleaner.clean_text(extraction_result['text'])
    
    # 4. 기본 통계
    text_stats = self.text_cleaner.get_text_stats(cleaned_text)
    
    # 5. 간단한 품질 점수
    quality_score = self._calculate_basic_quality(text_stats)
    
    # 6. DB 저장 (정제된 텍스트만)
    refined_data = {
        'brand_id': data['brand_id'],
        'source_table': 'web',
        'source_id': data['id'],
        'source_url': data['url'],
        'refined_text': cleaned_text,
        'word_count': text_stats['word_count'],
        'sentence_count': text_stats['sentence_count'],
        'quality_score': quality_score,
        'refiner_version': REFINER_VERSION
    }
```

## 이점
1. **처리 속도 향상** - 불필요한 분석 제거
2. **중복 제거** - Agent 10과 역할 명확히 구분
3. **파이프라인 효율성** - 각 에이전트가 전문화된 작업만 수행
4. **유지보수 용이** - 코드 간소화

## 데이터 흐름
```
Agent 02 (크롤링) 
    ↓ raw HTML
Agent 06 (정제) - HTML→텍스트 변환만
    ↓ clean text
Agent 10 (키워드) - 엔티티/컨셉/쿼리 추출
    ↓ keywords
Agent 12 (프롬프트 생성)
```