"""
Brand-related database queries
"""
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

from ..utils import get_db
from ..config import Tables

class BrandQueries:
    """Queries for brand, channel, and product operations"""
    
    @staticmethod
    def create_brand(brand_data: Dict[str, Any]) -> int:
        """Create a new brand"""
        db = get_db()
        
        # Convert lists/dicts to JSON strings
        json_fields = ['primary_demographics', 
                      'geographic_targets', 'brand_personality']
        for field in json_fields:
            if field in brand_data and brand_data[field] is not None:
                brand_data[field] = json.dumps(brand_data[field], ensure_ascii=False)
        
        return db.insert(Tables.BRANDS, brand_data)
    
    @staticmethod
    def get_brand_by_id(brand_id: int) -> Optional[Dict[str, Any]]:
        """Get brand by ID"""
        db = get_db()
        query = f"SELECT * FROM {Tables.BRANDS} WHERE id = %s"
        result = db.execute_one(query, (brand_id,))
        
        if result:
            # Parse JSON fields
            json_fields = ['primary_demographics', 
                          'geographic_targets', 'brand_personality']
            for field in json_fields:
                if result.get(field):
                    result[field] = json.loads(result[field])
        
        return result
    
    @staticmethod
    def get_brand_by_name(brand_name: str) -> Optional[Dict[str, Any]]:
        """Get brand by official name"""
        db = get_db()
        query = f"SELECT * FROM {Tables.BRANDS} WHERE brand_official_name = %s"
        result = db.execute_one(query, (brand_name,))
        
        if result:
            # Parse JSON fields
            json_fields = []
            for field in json_fields:
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except:
                        pass
        
        return result
    
    @staticmethod
    def update_brand(brand_id: int, updates: Dict[str, Any]) -> int:
        """Update brand information"""
        db = get_db()
        
        # Convert JSON fields
        json_fields = ['primary_demographics', 
                      'geographic_targets', 'brand_personality']
        for field in json_fields:
            if field in updates and updates[field] is not None:
                updates[field] = json.dumps(updates[field], ensure_ascii=False)
        
        return db.update(Tables.BRANDS, updates, "id = %s", (brand_id,))
    
    @staticmethod
    def list_01_brands(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List 01_brands with optional filters"""
        db = get_db()
        query = f"SELECT * FROM {Tables.BRANDS} WHERE 1=1"
        params = []
        
        if filters:
            if 'hq_country' in filters:
                query += " AND hq_country = %s"
                params.append(filters['hq_country'])
            
            if 'price_positioning' in filters:
                query += " AND price_positioning = %s"
                params.append(filters['price_positioning'])
        
        query += " ORDER BY brand_official_name"
        return db.execute(query, tuple(params) if params else None)
    
    # Brand Channels
    @staticmethod
    def create_or_update_channels(brand_id: int, channel_data: Dict[str, Any]) -> int:
        """Create or update brand channels"""
        db = get_db()
        
        # Check if channels exist
        existing = db.execute_one(
            f"SELECT id FROM {Tables.BRAND_CHANNELS} WHERE brand_id = %s", 
            (brand_id,)
        )
        
        # Convert eshop_urls to JSON if needed
        if 'eshop_urls' in channel_data and isinstance(channel_data['eshop_urls'], list):
            channel_data['eshop_urls'] = json.dumps(channel_data['eshop_urls'], ensure_ascii=False)
        
        if existing:
            # Update
            return db.update(
                Tables.BRAND_CHANNELS, 
                channel_data, 
                "brand_id = %s", 
                (brand_id,)
            )
        else:
            # Insert
            channel_data['brand_id'] = brand_id
            return db.insert(Tables.BRAND_CHANNELS, channel_data)
    
    @staticmethod
    def get_brand_channels(brand_id: int) -> Optional[Dict[str, Any]]:
        """Get brand channels - Now retrieves from 01_brands table"""
        db = get_db()
        query = f"""
        SELECT 
            id,
            official_site_url,
            instagram_handle,
            brand_official_name,
            brand_name_korean,
            brand_name_english
        FROM {Tables.BRANDS} 
        WHERE id = %s 
        ORDER BY updated_at DESC
        LIMIT 1
        """
        result = db.execute_one(query, (brand_id,))
        
        # Transform to match old format for compatibility
        if result:
            return {
                'brand_id': result['id'],
                'official_site_url': result['official_site_url'],
                'instagram_handle': result['instagram_handle'],
                'brand_name': result['brand_official_name']
            }
        
        return None
    
    @staticmethod
    def get_brand_urls(brand_id: int) -> Optional[Dict[str, Any]]:
        """Get brand URLs from 01_brands table"""
        db = get_db()
        query = f"""
        SELECT 
            id,
            official_site_url,
            instagram_handle,
            brand_official_name,
            brand_name_korean,
            brand_name_english
        FROM {Tables.BRANDS} 
        WHERE id = %s 
        ORDER BY updated_at DESC
        LIMIT 1
        """
        return db.execute_one(query, (brand_id,))
    
    # Products
    @staticmethod
    def create_product(product_data: Dict[str, Any]) -> int:
        """Create a new product"""
        db = get_db()
        
        # Convert JSON fields
        json_fields = ['core_categories', 'materials_focus', 'design_elements',
                      'colorways', 'sizes_available', 'image_urls', 'product_json']
        for field in json_fields:
            if field in product_data and product_data[field] is not None:
                product_data[field] = json.dumps(product_data[field], ensure_ascii=False)
        
        return db.insert(Tables.PRODUCTS, product_data)
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        db = get_db()
        query = f"SELECT * FROM {Tables.PRODUCTS} WHERE id = %s"
        result = db.execute_one(query, (product_id,))
        
        if result:
            # Parse JSON fields
            json_fields = ['core_categories', 'materials_focus', 'design_elements',
                          'colorways', 'sizes_available', 'image_urls', 'product_json']
            for field in json_fields:
                if result.get(field):
                    result[field] = json.loads(result[field])
        
        return result
    
    @staticmethod
    def list_products(brand_id: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List products for a brand"""
        db = get_db()
        query = f"SELECT * FROM {Tables.PRODUCTS} WHERE brand_id = %s"
        params = [brand_id]
        
        if filters:
            if 'season' in filters:
                query += " AND season = %s"
                params.append(filters['season'])
            
            if 'inventory_status' in filters:
                query += " AND inventory_status = %s"
                params.append(filters['inventory_status'])
            
            if 'is_active' in filters:
                query += " AND is_active = %s"
                params.append(filters['is_active'])
        
        query += " ORDER BY created_at DESC"
        return db.execute(query, tuple(params))
    
    @staticmethod
    def update_product(product_id: int, updates: Dict[str, Any]) -> int:
        """Update product information"""
        db = get_db()
        
        # Convert JSON fields
        json_fields = ['core_categories', 'materials_focus', 'design_elements',
                      'colorways', 'sizes_available', 'image_urls', 'product_json']
        for field in json_fields:
            if field in updates and updates[field] is not None:
                updates[field] = json.dumps(updates[field], ensure_ascii=False)
        
        return db.update(Tables.PRODUCTS, updates, "id = %s", (product_id,))
    
    @staticmethod
    def search_products(brand_id: int, search_term: str) -> List[Dict[str, Any]]:
        """Search products by name"""
        db = get_db()
        query = f"""
        SELECT * FROM {Tables.PRODUCTS} 
        WHERE brand_id = %s AND MATCH(product_name) AGAINST(%s IN NATURAL LANGUAGE MODE)
        ORDER BY MATCH(product_name) AGAINST(%s IN NATURAL LANGUAGE MODE) DESC
        """
        return db.execute(query, (brand_id, search_term, search_term))
    
    @staticmethod
    def get_brand_statistics(brand_id: int) -> Dict[str, Any]:
        """Get brand statistics"""
        db = get_db()
        
        stats = {}
        
        # Product count
        query = f"SELECT COUNT(*) as count FROM {Tables.PRODUCTS} WHERE brand_id = %s"
        result = db.execute_one(query, (brand_id,))
        stats['total_products'] = result['count']
        
        # Active products
        query = f"SELECT COUNT(*) as count FROM {Tables.PRODUCTS} WHERE brand_id = %s AND is_active = TRUE"
        result = db.execute_one(query, (brand_id,))
        stats['active_products'] = result['count']
        
        # Average price
        query = f"SELECT AVG(price) as avg_price FROM {Tables.PRODUCTS} WHERE brand_id = %s AND price > 0"
        result = db.execute_one(query, (brand_id,))
        stats['avg_price'] = float(result['avg_price']) if result['avg_price'] else 0
        
        # Content count by platform
        for platform in ['web', 'instagram', 'naver', 'tistory']:
            query = f"""
            SELECT COUNT(*) as count 
            FROM refined_content 
            WHERE brand_id = %s AND source_table = %s
            """
            result = db.execute_one(query, (brand_id, platform))
            stats[f'{platform}_content_count'] = result['count']
        
        return stats