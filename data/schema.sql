-- College Compass Database Schema
-- This file contains the complete database schema for the College Compass application.
-- To set up a new environment, run this script to create all necessary tables.
-- Last updated: January 2, 2025

-- =============================================
-- Core User Management Tables
-- =============================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,  -- User's email address, used for login
    name VARCHAR(255) NOT NULL,          -- User's display name
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,  -- One profile per user
    gpa FLOAT,                                    -- Academic GPA
    interests TEXT[],                             -- Array of academic/extracurricular interests
    activities TEXT[],                            -- Array of extracurricular activities
    target_majors TEXT[],                         -- Array of intended majors
    target_schools TEXT[],                        -- Array of target institutions
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- Achievement System Tables
-- Used to gamify the college application process
-- =============================================

CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,  -- Unique name of the achievement
    description TEXT NOT NULL,          -- Detailed description of how to earn the achievement
    icon_name VARCHAR(100) NOT NULL,    -- Name of the icon to display (e.g., '🎓', '📚')
    points INTEGER DEFAULT 0,           -- Points awarded for earning this achievement
    category VARCHAR(50) NOT NULL,      -- Category (e.g., 'Academic', 'Application', 'Research')
    requirements JSONB NOT NULL,        -- JSON object containing achievement requirements
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_achievements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    achievement_id INTEGER REFERENCES achievements(id),
    progress JSONB NOT NULL DEFAULT '{}',        -- JSON object tracking progress towards completion
    completed BOOLEAN DEFAULT FALSE,             -- Whether the achievement has been earned
    completed_at TIMESTAMP,                      -- When the achievement was earned
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, achievement_id)              -- User can't earn same achievement twice
);

-- =============================================
-- AI Chat System Tables
-- Stores chat history and sessions for the AI counselor
-- =============================================

CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),  -- User who owns this chat session
    title VARCHAR(255),                    -- Display title for the chat session
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id),  -- Chat session this message belongs to
    content TEXT,                                     -- Message content
    role VARCHAR(50),                                 -- Message sender ('user' or 'assistant')
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- College Application Management Tables
-- Core tables for managing college applications
-- =============================================

CREATE TABLE institutions (
    unitid INTEGER PRIMARY KEY,              -- Unique identifier from IPEDS
    institution_name VARCHAR(255) NOT NULL,   -- Official name of the institution
    city VARCHAR(100) NOT NULL,              -- City where institution is located
    state_abbreviation CHAR(2) NOT NULL,     -- Two-letter state code
    zip VARCHAR(10),                         -- ZIP code
    geographic_region VARCHAR(100),          -- Geographic region
    control_of_institution VARCHAR(50),      -- Public, Private non-profit, Private for-profit
    degree_levels JSONB,                     -- Array of degree levels offered
    program_offerings JSONB,                 -- Array of programs/majors offered
    tuition_and_fees DECIMAL(10,2),         -- Annual tuition and fees
    typical_housing_charge DECIMAL(10,2),    -- Annual housing cost
    additional_information TEXT,             -- Any additional details
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE college_matches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    matches JSONB NOT NULL,              -- JSON object containing match details and scores
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_favorite_institutions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    institution_id INTEGER REFERENCES institutions(unitid),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, institution_id)
);

-- =============================================
-- Application Timeline and Deadline Management
-- =============================================

CREATE TABLE application_deadlines (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    college_name VARCHAR(255) NOT NULL,
    deadline_type VARCHAR(50) NOT NULL,   -- Type of deadline (e.g., 'Early Decision', 'Regular')
    deadline_date DATE NOT NULL,
    requirements JSONB NOT NULL DEFAULT '{}',  -- Required materials and their status
    status VARCHAR(50) DEFAULT 'pending',      -- Application status
    notes TEXT,                               -- User notes about the application
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE timeline_milestones (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date DATE NOT NULL,
    category VARCHAR(50) NOT NULL,          -- Type of milestone
    priority VARCHAR(20) DEFAULT 'medium',   -- Priority level
    status VARCHAR(50) DEFAULT 'pending',    -- Completion status
    completion_date TIMESTAMP,               -- When milestone was completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE deadline_reminders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    deadline_id INTEGER REFERENCES application_deadlines(id),
    reminder_date TIMESTAMP NOT NULL,        -- When to send the reminder
    reminder_type VARCHAR(50) NOT NULL,      -- Type of reminder (email, notification)
    is_sent BOOLEAN DEFAULT FALSE,           -- Whether reminder has been sent
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- Internship Management System
-- =============================================

CREATE TABLE internship_programs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    organization VARCHAR(255) NOT NULL,
    description TEXT,
    website_url TEXT,
    program_type VARCHAR(50),                -- Type of program (research, internship, etc.)
    subject_areas TEXT[],                    -- Academic areas covered
    grade_levels TEXT[],                     -- Eligible grade levels
    application_deadline DATE,
    program_duration VARCHAR(100),           -- Duration of the program
    location_type VARCHAR(50),               -- Remote, in-person, hybrid
    locations TEXT[],                        -- Array of program locations
    requirements JSONB,                      -- Detailed program requirements
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE internship_applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    program_id INTEGER REFERENCES internship_programs(id),
    status VARCHAR(50) DEFAULT 'interested',  -- Application status
    application_date DATE,                    -- When application was submitted
    notes TEXT,                              -- User notes about application
    documents JSONB DEFAULT '{}',            -- Tracks required documents
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, program_id)              -- Prevent duplicate applications
);

-- =============================================
-- Performance Optimization Indices
-- =============================================

-- User-related indices
CREATE INDEX idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX idx_profiles_user_id ON profiles(user_id);

-- Chat system indices
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_messages_session_id ON messages(session_id);

-- College application indices
CREATE INDEX idx_institutions_name ON institutions(institution_name);
CREATE INDEX idx_institutions_state ON institutions(state_abbreviation);
CREATE INDEX idx_college_matches_user_id ON college_matches(user_id);
CREATE INDEX idx_user_favorite_institutions_user_id ON user_favorite_institutions(user_id);

-- Timeline and deadline indices
CREATE INDEX idx_application_deadlines_user_id ON application_deadlines(user_id);
CREATE INDEX idx_timeline_milestones_user_id ON timeline_milestones(user_id);
CREATE INDEX idx_deadline_reminders_deadline_id ON deadline_reminders(deadline_id);

-- Internship system indices
CREATE INDEX idx_internship_applications_user_id ON internship_applications(user_id);
CREATE INDEX idx_internship_programs_deadline ON internship_programs(application_deadline);
CREATE INDEX idx_user_achievements_achievement_id ON user_achievements(achievement_id);


-- =============================================
-- Notes on Usage
-- =============================================
-- 1. This schema should be run on a fresh database to set up the College Compass application
-- 2. Indexes are created for optimal query performance on frequently accessed fields
-- 3. JSONB fields are used for flexible data structures (requirements, documents, etc.)
-- 4. Array fields (TEXT[]) are used for simple lists that don't require complex querying
-- 5. Timestamps are automatically set using DEFAULT CURRENT_TIMESTAMP
-- 6. Foreign key constraints ensure data integrity across tables