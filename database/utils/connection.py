"""
Database Connection Manager
"""
import pymysql
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple
from pymysql.cursors import DictCursor
from datetime import datetime
import time

from ..config import db_config, QUERY_TIMEOUTS

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Database connection manager with connection pooling simulation"""
    
    def __init__(self, config=None):
        self.config = config or db_config
        self._connection: Optional[pymysql.Connection] = None
        self._transaction_active = False
        
    def connect(self) -> pymysql.Connection:
        """Create a database connection"""
        try:
            connection = pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                charset=self.config.charset,
                cursorclass=DictCursor,
                autocommit=False
            )
            logger.info(f"Connected to database: {self.config.database}")
            return connection
        except pymysql.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def get_connection(self) -> pymysql.Connection:
        """Get or create a connection"""
        if self._connection is None or not self._connection.open:
            self._connection = self.connect()
        else:
            # Ping to check if connection is alive
            try:
                self._connection.ping(reconnect=True)
            except:
                self._connection = self.connect()
        return self._connection
    
    def close(self):
        """Close the connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")
    
    @contextmanager
    def transaction(self):
        """Transaction context manager"""
        connection = self.get_connection()
        try:
            self._transaction_active = True
            yield connection
            connection.commit()
            logger.debug("Transaction committed")
        except Exception as e:
            connection.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
        finally:
            self._transaction_active = False
    
    @contextmanager
    def cursor(self, cursor_class=DictCursor):
        """Cursor context manager"""
        connection = self.get_connection()
        cursor = connection.cursor(cursor_class)
        try:
            yield cursor
            if not self._transaction_active:
                connection.commit()
        except Exception as e:
            if not self._transaction_active:
                connection.rollback()
            raise
        finally:
            cursor.close()
    
    def execute(self, query: str, params: Optional[Tuple] = None, 
                timeout: Optional[int] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results"""
        timeout = timeout or QUERY_TIMEOUTS['default']
        start_time = time.time()
        
        with self.cursor() as cursor:
            cursor.execute(f"SET SESSION MAX_EXECUTION_TIME={timeout * 1000}")
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            execution_time = time.time() - start_time
            if execution_time > self.config.slow_query_threshold:
                logger.warning(f"Slow query ({execution_time:.2f}s): {query[:100]}...")
            
            return results
    
    def execute_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
        """Execute a SELECT query and return one result"""
        with self.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """Execute many INSERT/UPDATE queries"""
        with self.cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insert a record and return the inserted ID"""
        columns = ', '.join(f"`{k}`" for k in data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
        
        with self.cursor() as cursor:
            cursor.execute(query, tuple(data.values()))
            return cursor.lastrowid
    
    def update(self, table: str, data: Dict[str, Any], 
               where: str, where_params: Optional[Tuple] = None) -> int:
        """Update records and return affected rows"""
        set_clause = ', '.join(f"`{k}` = %s" for k in data.keys())
        query = f"UPDATE `{table}` SET {set_clause} WHERE {where}"
        params = tuple(data.values()) + (where_params or ())
        
        with self.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def delete(self, table: str, where: str, where_params: Optional[Tuple] = None) -> int:
        """Delete records and return affected rows"""
        query = f"DELETE FROM `{table}` WHERE {where}"
        
        with self.cursor() as cursor:
            cursor.execute(query, where_params)
            return cursor.rowcount
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        query = """
        SELECT COUNT(*) as count
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = %s
        """
        result = self.execute_one(query, (self.config.database, table_name))
        return result['count'] > 0
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table column information"""
        query = """
        SELECT 
            COLUMN_NAME as name,
            DATA_TYPE as type,
            IS_NULLABLE as nullable,
            COLUMN_DEFAULT as default_value,
            COLUMN_KEY as key,
            EXTRA as extra
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ORDINAL_POSITION
        """
        return self.execute(query, (self.config.database, table_name))

# Global connection instance
_db_connection = None

def get_db() -> DatabaseConnection:
    """Get the global database connection"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection

@contextmanager
def get_db_cursor():
    """Get a database cursor context manager"""
    db = get_db()
    with db.cursor() as cursor:
        yield cursor

def close_db():
    """Close the global database connection"""
    global _db_connection
    if _db_connection:
        _db_connection.close()
        _db_connection = None