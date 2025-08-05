-- Migration: Drop brand_domain_tree column from 01_brands table
-- Date: 2025-07-25
-- Description: Remove unused brand_domain_tree column that stored hierarchical domain structure

-- Drop the column
ALTER TABLE modular_agents_db.01_brands 
DROP COLUMN IF EXISTS brand_domain_tree;

-- Note: This column stored JSON data for brand domain hierarchy
-- but is no longer needed in the current implementation