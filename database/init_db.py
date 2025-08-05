#!/usr/bin/env python3
"""
Database Initialization Script
Executes all SQL schema files in the correct order
"""
import os
import sys
import logging
import pymysql
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import db_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Initialize database with schema files"""
    
    def __init__(self):
        self.schema_dir = Path(__file__).parent / 'schema'
        self.connection = None
        
    def connect_without_db(self) -> pymysql.Connection:
        """Connect to MySQL without selecting a database"""
        return pymysql.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            charset=db_config.charset
        )
    
    def connect_with_db(self) -> pymysql.Connection:
        """Connect to MySQL with database selected"""
        return pymysql.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
            charset=db_config.charset
        )
    
    def get_schema_files(self) -> List[Path]:
        """Get all SQL files in order"""
        sql_files = sorted(self.schema_dir.glob('*.sql'))
        return sql_files
    
    def execute_sql_file(self, file_path: Path, connection: pymysql.Connection):
        """Execute a SQL file"""
        logger.info(f"Executing {file_path.name}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split by delimiter to handle stored procedures
        statements = []
        current_statement = []
        in_delimiter = False
        delimiter = ';'
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # Check for DELIMITER command
            if line.upper().startswith('DELIMITER'):
                new_delimiter = line.split()[1]
                if new_delimiter != delimiter:
                    delimiter = new_delimiter
                    in_delimiter = True
                else:
                    in_delimiter = False
                continue
            
            if line:
                current_statement.append(line)
                
                # Check if statement ends with delimiter
                if line.endswith(delimiter):
                    statement = '\n'.join(current_statement)
                    # Remove delimiter from end
                    statement = statement[:-len(delimiter)].strip()
                    if statement:
                        statements.append(statement)
                    current_statement = []
        
        # Execute statements
        with connection.cursor() as cursor:
            for statement in statements:
                if statement.strip():
                    try:
                        cursor.execute(statement)
                        connection.commit()
                    except pymysql.Error as e:
                        logger.error(f"Error executing statement: {e}")
                        logger.error(f"Statement: {statement[:100]}...")
                        raise
        
        logger.info(f"Successfully executed {file_path.name}")
    
    def initialize(self, force: bool = False):
        """Initialize the database"""
        try:
            # First check if database exists
            conn = self.connect_without_db()
            with conn.cursor() as cursor:
                cursor.execute(f"SHOW DATABASES LIKE '{db_config.database}'")
                exists = cursor.fetchone() is not None
            
            if exists and not force:
                logger.warning(f"Database '{db_config.database}' already exists!")
                response = input("Do you want to drop and recreate it? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Initialization cancelled")
                    return
                
                # Drop existing database
                cursor.execute(f"DROP DATABASE {db_config.database}")
                logger.info(f"Dropped existing database '{db_config.database}'")
            
            conn.close()
            
            # Get schema files
            schema_files = self.get_schema_files()
            if not schema_files:
                logger.error("No schema files found!")
                return
            
            logger.info(f"Found {len(schema_files)} schema files")
            
            # Execute initialization file first (creates database)
            init_file = self.schema_dir / '00_database_init.sql'
            if init_file.exists():
                conn = self.connect_without_db()
                self.execute_sql_file(init_file, conn)
                conn.close()
            
            # Execute remaining schema files
            conn = self.connect_with_db()
            for sql_file in schema_files:
                if sql_file.name != '00_database_init.sql':
                    self.execute_sql_file(sql_file, conn)
            
            logger.info("Database initialization completed successfully!")
            
            # Show created tables
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                logger.info(f"Created {len(tables)} tables:")
                for table in tables:
                    table_name = list(table.values())[0]
                    logger.info(f"  - {table_name}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
        finally:
            if self.connection:
                self.connection.close()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize Modular Agents Database')
    parser.add_argument('--force', '-f', action='store_true', 
                       help='Force recreate database without confirmation')
    parser.add_argument('--check', '-c', action='store_true',
                       help='Check if database exists without creating')
    
    args = parser.parse_args()
    
    if args.check:
        try:
            conn = pymysql.connect(
                host=db_config.host,
                port=db_config.port,
                user=db_config.user,
                password=db_config.password,
                charset=db_config.charset
            )
            with conn.cursor() as cursor:
                cursor.execute(f"SHOW DATABASES LIKE '{db_config.database}'")
                exists = cursor.fetchone() is not None
            
            if exists:
                logger.info(f"Database '{db_config.database}' exists")
                # Show tables
                conn = pymysql.connect(
                    host=db_config.host,
                    port=db_config.port,
                    user=db_config.user,
                    password=db_config.password,
                    database=db_config.database,
                    charset=db_config.charset
                )
                with conn.cursor() as cursor:
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    logger.info(f"Found {len(tables)} tables")
            else:
                logger.info(f"Database '{db_config.database}' does not exist")
                
            conn.close()
        except Exception as e:
            logger.error(f"Check failed: {e}")
            sys.exit(1)
    else:
        initializer = DatabaseInitializer()
        try:
            initializer.initialize(force=args.force)
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()