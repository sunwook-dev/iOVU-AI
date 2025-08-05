-- ============================================
-- Database Initialization Script
-- ============================================
-- Description: Creates the main database and sets up initial configurations
-- Author: Modular Agents System
-- Created: 2025-07-21
-- ============================================

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS modular_agents_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Use the database
USE modular_agents_db;

-- Set timezone to Seoul
SET time_zone = '+09:00';

-- ============================================
-- Database Configuration
-- ============================================

-- Enable strict mode for data integrity
SET GLOBAL sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- Set connection charset
SET NAMES utf8mb4;

-- ============================================
-- Create schema version tracking table
-- ============================================
CREATE TABLE IF NOT EXISTS schema_versions (
    version_id INT AUTO_INCREMENT PRIMARY KEY,
    version_number VARCHAR(20) NOT NULL UNIQUE,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(100) DEFAULT USER()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert initial version
INSERT INTO schema_versions (version_number, description) 
VALUES ('1.0.0', 'Initial database schema creation');

-- ============================================
-- Utility Functions
-- ============================================

-- Function to generate UUID
DELIMITER $$
CREATE FUNCTION IF NOT EXISTS generate_uuid() RETURNS CHAR(36)
DETERMINISTIC
BEGIN
    RETURN UUID();
END$$
DELIMITER ;

-- ============================================
-- Grant Permissions (adjust as needed)
-- ============================================
-- Example: GRANT ALL PRIVILEGES ON modular_agents_db.* TO 'app_user'@'localhost';