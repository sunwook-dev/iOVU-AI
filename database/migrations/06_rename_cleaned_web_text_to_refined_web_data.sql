-- Migration: Rename cleaned_web_text to 06_refined_web_data
-- Date: 2025-07-25
-- Description: Rename cleaned_web_text table to follow agent numbering convention

-- Step 1: Drop foreign key constraint from prompt_keywords table
ALTER TABLE modular_agents_db.prompt_keywords 
DROP FOREIGN KEY fk_prompt_keywords_cleaned_web_text;

-- Step 2: Rename the table
ALTER TABLE modular_agents_db.cleaned_web_text 
RENAME TO modular_agents_db.`06_refined_web_data`;

-- Step 3: Recreate foreign key constraint with new table name
ALTER TABLE modular_agents_db.prompt_keywords
ADD CONSTRAINT fk_prompt_keywords_refined_web_data 
FOREIGN KEY (cleaned_web_text_id) 
REFERENCES `06_refined_web_data`(id) 
ON DELETE CASCADE;

-- Note: Indexes and other constraints are automatically updated with table rename
-- The FULLTEXT index on cleaned_text column will be preserved