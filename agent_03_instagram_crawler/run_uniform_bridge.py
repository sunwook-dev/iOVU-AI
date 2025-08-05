#!/usr/bin/env python3
"""Direct crawler for uniform_bridge without database"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from crawler import InstagramCrawler, Config

async def crawl_uniform_bridge():
    """Crawl uniform_bridge directly"""
    # Ensure data directory exists
    Config.ensure_data_dirs()
    
    # Create crawler instance
    crawler = InstagramCrawler()
    
    print(f"Starting Instagram crawler for @uniform_bridge")
    print(f"Max scroll rounds: {Config.MAX_SCROLL_ROUND}")
    print(f"Batch size: {Config.CRAWL_BATCH_SIZE}")
    print(f"Data directory: {Config.DATA_DIR}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Login
            await crawler.login(page)
            
            instagram_handle = "uniform_bridge"
            print(f"\n[*] Crawling Instagram: @{instagram_handle}")
            
            # Crawl main posts
            target_url = f"https://www.instagram.com/{instagram_handle}/"
            posts_data = await crawler.crawl_posts(
                page, target_url, instagram_handle, 
                max_scroll_round=Config.MAX_SCROLL_ROUND,
                crawl_batch_size=Config.CRAWL_BATCH_SIZE
            )
            
            print(f"\n✅ Crawled {len(posts_data)} main posts")
            
            # Crawl tagged posts
            tagged_url = f"https://www.instagram.com/{instagram_handle}/tagged/"
            tagged_data = await crawler.crawl_posts(
                page, tagged_url, instagram_handle,
                max_scroll_round=Config.MAX_SCROLL_ROUND,
                crawl_batch_size=Config.CRAWL_BATCH_SIZE,
                file_suffix="tagged"
            )
            
            print(f"✅ Crawled {len(tagged_data)} tagged posts")
            
            # Show sample data
            if posts_data:
                print(f"\n📊 Sample post data:")
                sample = posts_data[0]
                print(f"   Date: {sample.get('date', 'N/A')}")
                print(f"   Content: {sample.get('content', 'N/A')[:100]}...")
                print(f"   Images: {len(sample.get('img', []))} images")
                print(f"   Comments: {len(sample.get('comments', []))} comments")
                
            print(f"\n✅ Data saved to:")
            print(f"   - {Config.DATA_DIR}/uniform_bridge.json")
            print(f"   - {Config.DATA_DIR}/uniform_bridge_tagged.json")
            
        except Exception as e:
            print(f"\n❌ Error during crawling: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(crawl_uniform_bridge())