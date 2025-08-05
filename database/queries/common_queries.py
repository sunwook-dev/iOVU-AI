"""
Common database queries for tracking, monitoring, and utilities
"""
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime, timedelta
from decimal import Decimal

from ..utils import get_db
from ..config import Tables

class CommonQueries:
    """Common queries for system monitoring and utilities"""
    
    # ========== Processing Pipeline ==========
    
    @staticmethod
    def create_pipeline(pipeline_data: Dict[str, Any]) -> int:
        """Create a new processing pipeline"""
        db = get_db()
        
        if 'pipeline_config' in pipeline_data and isinstance(pipeline_data['pipeline_config'], dict):
            pipeline_data['pipeline_config'] = json.dumps(
                pipeline_data['pipeline_config'], ensure_ascii=False
            )
        
        return db.insert(Tables.PROCESSING_PIPELINE, pipeline_data)
    
    @staticmethod
    def update_pipeline(pipeline_id: int, updates: Dict[str, Any]) -> int:
        """Update pipeline status and progress"""
        db = get_db()
        
        # Auto-update timestamps
        if 'status' in updates:
            if updates['status'] == 'running' and 'started_at' not in updates:
                updates['started_at'] = datetime.now()
            elif updates['status'] in ['completed', 'failed', 'cancelled']:
                if 'completed_at' not in updates:
                    updates['completed_at'] = datetime.now()
        
        if 'error_details' in updates and isinstance(updates['error_details'], list):
            updates['error_details'] = json.dumps(updates['error_details'], ensure_ascii=False)
        
        return db.update(Tables.PROCESSING_PIPELINE, updates, "id = %s", (pipeline_id,))
    
    @staticmethod
    def get_pipeline_status(pipeline_id: int) -> Optional[Dict[str, Any]]:
        """Get pipeline status"""
        db = get_db()
        query = f"SELECT * FROM {Tables.PROCESSING_PIPELINE} WHERE id = %s"
        result = db.execute_one(query, (pipeline_id,))
        
        if result:
            if result.get('pipeline_config'):
                result['pipeline_config'] = json.loads(result['pipeline_config'])
            if result.get('error_details'):
                result['error_details'] = json.loads(result['error_details'])
        
        return result
    
    @staticmethod
    def get_active_pipelines(brand_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get active pipelines"""
        db = get_db()
        query = f"""
        SELECT p.*, b.brand_official_name
        FROM {Tables.PROCESSING_PIPELINE} p
        LEFT JOIN {Tables.BRANDS} b ON p.brand_id = b.id
        WHERE p.status IN ('pending', 'running', 'paused')
        """
        params = []
        
        if brand_id:
            query += " AND p.brand_id = %s"
            params.append(brand_id)
        
        query += " ORDER BY p.created_at DESC"
        return db.execute(query, tuple(params) if params else None)
    
    # ========== Stage Logs ==========
    
    @staticmethod
    def create_stage_log(log_data: Dict[str, Any]) -> int:
        """Create a stage log entry"""
        db = get_db()
        
        json_fields = ['log_messages', 'error_details']
        for field in json_fields:
            if field in log_data and log_data[field] is not None:
                log_data[field] = json.dumps(log_data[field], ensure_ascii=False)
        
        log_data['started_at'] = datetime.now()
        return db.insert(Tables.STAGE_LOGS, log_data)
    
    @staticmethod
    def update_stage_log(log_id: int, updates: Dict[str, Any]) -> int:
        """Update stage log"""
        db = get_db()
        
        if 'status' in updates and updates['status'] in ['completed', 'failed']:
            updates['completed_at'] = datetime.now()
        
        json_fields = ['log_messages', 'error_details']
        for field in json_fields:
            if field in updates and updates[field] is not None:
                updates[field] = json.dumps(updates[field], ensure_ascii=False)
        
        return db.update(Tables.STAGE_LOGS, updates, "id = %s", (log_id,))
    
    # ========== API Usage Tracking ==========
    
    @staticmethod
    def track_api_usage(usage_data: Dict[str, Any]) -> int:
        """Track API usage"""
        db = get_db()
        
        # Calculate total cost if not provided
        if 'total_cost_usd' not in usage_data:
            input_cost = Decimal(str(usage_data.get('input_cost_usd', 0)))
            output_cost = Decimal(str(usage_data.get('output_cost_usd', 0)))
            usage_data['total_cost_usd'] = float(input_cost + output_cost)
        
        # Convert cost to KRW if exchange rate provided
        if 'exchange_rate' in usage_data and usage_data['total_cost_usd']:
            usage_data['cost_krw'] = float(
                Decimal(str(usage_data['total_cost_usd'])) * 
                Decimal(str(usage_data['exchange_rate']))
            )
        
        return db.insert(Tables.API_USAGE_TRACKING, usage_data)
    
    @staticmethod
    def get_api_usage_summary(brand_id: Optional[int] = None, 
                             days: int = 7) -> Dict[str, Any]:
        """Get API usage summary"""
        db = get_db()
        
        date_threshold = datetime.now() - timedelta(days=days)
        
        # Base query
        base_conditions = "WHERE created_at >= %s"
        params = [date_threshold]
        
        if brand_id:
            base_conditions += " AND brand_id = %s"
            params.append(brand_id)
        
        # Total usage by service
        query = f"""
        SELECT 
            service,
            COUNT(*) as request_count,
            SUM(total_tokens) as total_tokens,
            SUM(total_cost_usd) as total_cost_usd,
            AVG(response_time_ms) as avg_response_time
        FROM {Tables.API_USAGE_TRACKING}
        {base_conditions}
        GROUP BY service
        """
        by_service = db.execute(query, tuple(params))
        
        # Daily usage
        query = f"""
        SELECT 
            DATE(created_at) as date,
            SUM(total_cost_usd) as daily_cost,
            COUNT(*) as request_count
        FROM {Tables.API_USAGE_TRACKING}
        {base_conditions}
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        """
        daily_usage = db.execute(query, tuple(params))
        
        # Error rate
        query = f"""
        SELECT 
            COUNT(CASE WHEN is_success = FALSE THEN 1 END) as failed_requests,
            COUNT(*) as total_requests
        FROM {Tables.API_USAGE_TRACKING}
        {base_conditions}
        """
        error_stats = db.execute_one(query, tuple(params))
        error_rate = (error_stats['failed_requests'] / error_stats['total_requests'] * 100 
                     if error_stats['total_requests'] > 0 else 0)
        
        return {
            'by_service': by_service,
            'daily_usage': daily_usage,
            'error_rate': error_rate,
            'total_requests': error_stats['total_requests']
        }
    
    # ========== Cost Management ==========
    
    @staticmethod
    def update_cost_summary(date: datetime.date, brand_id: Optional[int] = None):
        """Update daily cost summary"""
        db = get_db()
        
        # Calculate costs for the day
        query = f"""
        SELECT 
            service,
            SUM(total_cost_usd) as cost,
            COUNT(*) as requests,
            SUM(total_tokens) as tokens
        FROM {Tables.API_USAGE_TRACKING}
        WHERE DATE(created_at) = %s
        """
        params = [date]
        
        if brand_id:
            query += " AND brand_id = %s"
            params.append(brand_id)
        
        query += " GROUP BY service"
        
        results = db.execute(query, tuple(params))
        
        if not results:
            return
        
        # Aggregate costs
        costs = {
            'openai_cost_usd': 0,
            'anthropic_cost_usd': 0,
            'other_api_cost_usd': 0,
            'total_requests': 0,
            'total_tokens': 0
        }
        
        for result in results:
            service = result['service']
            cost = float(result['cost'])
            
            if service == 'openai':
                costs['openai_cost_usd'] += cost
            elif service == 'anthropic':
                costs['anthropic_cost_usd'] += cost
            else:
                costs['other_api_cost_usd'] += cost
            
            costs['total_requests'] += result['requests']
            costs['total_tokens'] += result['tokens'] or 0
        
        costs['total_cost_usd'] = (
            costs['openai_cost_usd'] + 
            costs['anthropic_cost_usd'] + 
            costs['other_api_cost_usd']
        )
        
        # Insert or update summary
        existing = db.execute_one(
            f"""SELECT id FROM {Tables.COST_SUMMARY} 
            WHERE brand_id {'= %s' if brand_id else 'IS NULL'} 
            AND summary_date = %s AND summary_type = 'daily'""",
            (brand_id, date) if brand_id else (date,)
        )
        
        summary_data = {
            'brand_id': brand_id,
            'summary_date': date,
            'summary_type': 'daily',
            **costs
        }
        
        if existing:
            db.update(
                Tables.COST_SUMMARY,
                costs,
                "id = %s",
                (existing['id'],)
            )
        else:
            db.insert(Tables.COST_SUMMARY, summary_data)
    
    @staticmethod
    def check_cost_alerts(brand_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Check for cost threshold violations"""
        alerts = []
        db = get_db()
        
        # Get thresholds from environment or defaults
        hourly_threshold = 10.0  # $10
        daily_threshold = 100.0  # $100
        
        # Check hourly costs
        query = f"""
        SELECT 
            brand_id,
            SUM(total_cost_usd) as hourly_cost
        FROM {Tables.API_USAGE_TRACKING}
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """
        
        if brand_id:
            query += " AND brand_id = %s"
            query += " GROUP BY brand_id"
            results = db.execute(query, (brand_id,))
        else:
            query += " GROUP BY brand_id"
            results = db.execute(query)
        
        for result in results:
            if result['hourly_cost'] > hourly_threshold:
                alerts.append({
                    'type': 'hourly_cost_exceeded',
                    'brand_id': result['brand_id'],
                    'cost': result['hourly_cost'],
                    'threshold': hourly_threshold
                })
        
        # Check daily costs
        query = f"""
        SELECT 
            brand_id,
            SUM(total_cost_usd) as daily_cost
        FROM {Tables.API_USAGE_TRACKING}
        WHERE DATE(created_at) = CURDATE()
        """
        
        if brand_id:
            query += " AND brand_id = %s"
            query += " GROUP BY brand_id"
            results = db.execute(query, (brand_id,))
        else:
            query += " GROUP BY brand_id"
            results = db.execute(query)
        
        for result in results:
            if result['daily_cost'] > daily_threshold:
                alerts.append({
                    'type': 'daily_cost_exceeded',
                    'brand_id': result['brand_id'],
                    'cost': result['daily_cost'],
                    'threshold': daily_threshold
                })
        
        return alerts
    
    # ========== Alerts ==========
    
    @staticmethod
    def create_alert(alert_data: Dict[str, Any]) -> int:
        """Create a system alert"""
        db = get_db()
        
        if 'details' in alert_data and isinstance(alert_data['details'], dict):
            alert_data['details'] = json.dumps(alert_data['details'], ensure_ascii=False)
        
        return db.insert(Tables.ALERTS, alert_data)
    
    @staticmethod
    def get_unread_alerts(brand_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get unread alerts"""
        db = get_db()
        query = f"""
        SELECT * FROM {Tables.ALERTS}
        WHERE is_read = FALSE AND is_resolved = FALSE
        """
        params = []
        
        if brand_id:
            query += " AND brand_id = %s"
            params.append(brand_id)
        
        query += " ORDER BY severity DESC, created_at DESC"
        results = db.execute(query, tuple(params) if params else None)
        
        # Parse JSON fields
        for result in results:
            if result.get('details'):
                result['details'] = json.loads(result['details'])
        
        return results
    
    @staticmethod
    def mark_alerts_read(alert_ids: List[int]) -> int:
        """Mark alerts as read"""
        db = get_db()
        
        if not alert_ids:
            return 0
        
        placeholders = ', '.join(['%s'] * len(alert_ids))
        query = f"""
        UPDATE {Tables.ALERTS}
        SET is_read = TRUE
        WHERE id IN ({placeholders})
        """
        
        with db.cursor() as cursor:
            cursor.execute(query, alert_ids)
            return cursor.rowcount
    
    # ========== System Metrics ==========
    
    @staticmethod
    def record_system_metrics(metrics: Dict[str, Any]) -> int:
        """Record system performance metrics"""
        db = get_db()
        metrics['metric_timestamp'] = datetime.now()
        return db.insert(Tables.SYSTEM_METRICS, metrics)
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Get system health status"""
        db = get_db()
        
        # Get latest metrics
        query = f"""
        SELECT * FROM {Tables.SYSTEM_METRICS}
        ORDER BY metric_timestamp DESC
        LIMIT 1
        """
        latest_metrics = db.execute_one(query)
        
        # Get active processes
        query = f"""
        SELECT 
            COUNT(CASE WHEN status = 'running' THEN 1 END) as running_pipelines,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_pipelines
        FROM {Tables.PROCESSING_PIPELINE}
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """
        pipeline_stats = db.execute_one(query)
        
        # Get error rate
        query = f"""
        SELECT 
            COUNT(CASE WHEN is_success = FALSE THEN 1 END) / COUNT(*) * 100 as error_rate
        FROM {Tables.API_USAGE_TRACKING}
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """
        error_stats = db.execute_one(query)
        
        return {
            'latest_metrics': latest_metrics,
            'pipeline_stats': pipeline_stats,
            'error_rate': float(error_stats['error_rate']) if error_stats['error_rate'] else 0,
            'timestamp': datetime.now()
        }