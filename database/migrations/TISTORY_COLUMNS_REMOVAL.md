# Tistory Table Column Removal Migration

## Overview
This migration removes unused columns from the `raw_tistory_data` table that are either not being populated or are handled elsewhere in the pipeline.

## Removed Columns
1. **has_code_block** (BOOLEAN) - Code block detection is handled by the refiner's CodeBlockHandler
2. **code_languages** (JSON) - Language detection is done during refinement
3. **view_count** (INT) - No API access to get actual view counts
4. **like_count** (INT) - No API access to get actual like counts  
5. **comment_count** (INT) - No API access to get actual comment counts
6. **is_private** (BOOLEAN) - Not used/available
7. **modified_at** (DATETIME) - Not available from Tistory crawling

## Files Modified

### SQL Files
1. `/database/migrations/remove_tistory_unused_columns.sql` - Migration script
2. `/database/schema/02_raw_data_tables.sql` - Updated table definition

### Python Files
1. `/agent_05_tistory_crawler/crawler.py` - Removed fields from data insertion
2. `/database/queries/data_queries.py` - Removed 'code_languages' from JSON fields
3. `/agent_09_tistory_refiner/database_queries.py` - Updated engagement metrics handling
4. `/agent_15_blog_geo/database/queries.py` - Set engagement metrics to 0

## Running the Migration

To apply this migration to your database:

```bash
mysql -u your_username -p modular_agents_db < /path/to/modular_agents/database/migrations/remove_tistory_unused_columns.sql
```

## Impact
- **Data Loss**: These columns contain no meaningful data (all zeros or nulls)
- **Code Changes**: All references to these columns have been removed
- **Functionality**: No loss of functionality - code analysis is still performed by the refiner

## Rollback
If you need to rollback this migration, you would need to:
1. Re-add the columns to the table
2. Revert the code changes
3. Note that the data in these columns was not meaningful, so no data restoration is needed