# Database Setup Guide

This directory contains the database schema and initialization scripts for the College Compass application.

## Files

- `schema.sql`: Complete database schema with tables, indices, and documentation
- `db_tables.sql`: Additional database configurations (if needed)
- `All_college_export.csv`: Source data for college institutions

## Setting Up a New Environment

1. Create a new PostgreSQL database
2. Run `schema.sql` to create all necessary tables:
   ```sql
   psql -d your_database_name -f schema.sql
   ```
3. Import initial college data:
   ```bash
   python3 data/import/college_data_importer.py
   ```

## Schema Overview

The database is organized into several logical sections:

1. Core User Management
   - Users and profiles
   - Authentication data

2. Achievement System
   - Achievement definitions
   - User progress tracking

3. AI Chat System
   - Chat sessions
   - Message history

4. College Application Management
   - Institution data
   - College matches
   - User favorites

5. Timeline Management
   - Application deadlines
   - Milestones
   - Reminders

6. Internship System
   - Program listings
   - Application tracking

## Data Types

- `JSONB`: Used for flexible data structures (requirements, documents)
- `TEXT[]`: Used for simple lists (interests, activities)
- `TIMESTAMP`: Used for all date/time fields with automatic default values
- `SERIAL`: Used for auto-incrementing primary keys

## Performance Optimization

The schema includes indices for:
- Foreign key relationships
- Frequently filtered fields
- Search fields
- Common join conditions

## Maintenance Notes

1. All tables use `created_at` timestamps
2. Tables tracking state changes include `updated_at` timestamps
3. Foreign key constraints ensure referential integrity
4. Unique constraints prevent duplicate data where appropriate

For detailed field descriptions and usage examples, see the comments in `schema.sql`.
