# Simplified Text Refiners (Agents 06-09)

## Overview
Agents 06-09 have been simplified to focus solely on text cleaning and basic statistics, removing all advanced features like sentiment analysis, entity extraction, and keyword analysis.

## Simplified Architecture

### Common Features
- Extract text from raw data
- Clean and normalize text
- Calculate basic statistics (word count, sentence count, unique word ratio)
- Save to platform-specific cleaned text tables

### Database Structure
```
cleaned_web_text       - Agent 06 (Web pages)
cleaned_instagram_text - Agent 07 (Instagram posts)
cleaned_naver_text     - Agent 08 (Naver blogs)
cleaned_tistory_text   - Agent 09 (Tistory blogs)
```

## Running the Simplified Agents

### Agent 06 - Web Refiner
```bash
cd agent_06_web_refiner
python run_web_refiner.py --limit 100
python run_web_refiner.py --stats
```

### Agent 07 - Instagram Refiner
```bash
cd agent_07_instagram_refiner
python run_instagram_refiner_new.py --limit 100
python run_instagram_refiner_new.py --stats
```

### Agent 08 - Naver Refiner
```bash
cd agent_08_naver_refiner
python run_naver_refiner_new.py --limit 100
python run_naver_refiner_new.py --stats
```

### Agent 09 - Tistory Refiner
```bash
cd agent_09_tistory_refiner
python run_tistory_refiner_new.py --limit 100
python run_tistory_refiner_new.py --stats
```

## Removed Features
- Sentiment analysis
- Entity extraction
- Topic modeling
- Quality scoring
- Relevance scoring
- Image processing
- Metadata processing
- Ad detection
- Complex content classification

## Files to Keep
- `run_[platform]_refiner_new.py` - Main execution script
- `database_queries_new.py` - Database operations
- `text_extractor_simple.py` or `text_extractor.py` - Text extraction
- `text_cleaner.py` - Text cleaning utilities

## Files to Remove (Legacy)
- `ad_detector.py`
- `image_processor.py`
- `metadata_processor.py`
- `quality_evaluator.py`
- `entity_extractor.py`
- `sentiment_analyzer.py`
- Old database_queries.py files
- Old run scripts