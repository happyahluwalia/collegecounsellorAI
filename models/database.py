import os
import psycopg2
import logging
import time
from psycopg2.extras import RealDictCursor
from utils.error_handling import DatabaseError, log_error

logger = logging.getLogger(__name__)

class Database:
    _instance = None
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize_connection()
        return cls._instance

    def _initialize_connection(self):
        """Initialize database connection with retry mechanism"""
        retry_count = 0
        while retry_count < self.MAX_RETRIES:
            try:
                self.conn = psycopg2.connect(
                    host=os.environ['PGHOST'],
                    database=os.environ['PGDATABASE'],
                    user=os.environ['PGUSER'],
                    password=os.environ['PGPASSWORD'],
                    port=os.environ['PGPORT']
                )
                logger.info("Database connection established successfully")
                self.create_tables()
                break
            except psycopg2.Error as e:
                retry_count += 1
                log_error(e, f"Database connection attempt {retry_count}")
                if retry_count >= self.MAX_RETRIES:
                    raise DatabaseError("Unable to connect to the database after multiple attempts")
                time.sleep(self.RETRY_DELAY)

    def _ensure_connection(self):
        """Ensure database connection is alive and reconnect if necessary"""
        try:
            # Test connection
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
        except (psycopg2.Error, AttributeError):
            logger.warning("Database connection lost, attempting to reconnect")
            self._initialize_connection()

    def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            with self.conn.cursor() as cur:
                # Create existing tables
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS achievements (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL UNIQUE,
                        description TEXT NOT NULL,
                        icon_name VARCHAR(100) NOT NULL,
                        points INTEGER DEFAULT 0,
                        category VARCHAR(50) NOT NULL,
                        requirements JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS profiles (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) UNIQUE,
                        gpa FLOAT,
                        interests TEXT[],
                        activities TEXT[],
                        target_majors TEXT[],
                        target_schools TEXT[],
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        title VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        session_id INTEGER REFERENCES chat_sessions(id),
                        content TEXT,
                        role VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS user_achievements (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        achievement_id INTEGER REFERENCES achievements(id),
                        progress JSONB NOT NULL DEFAULT '{}',
                        completed BOOLEAN DEFAULT FALSE,
                        completed_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, achievement_id)
                    );

                    CREATE TABLE IF NOT EXISTS college_matches (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        matches JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- New tables for timeline and deadline tracking
                    CREATE TABLE IF NOT EXISTS application_deadlines (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        college_name VARCHAR(255) NOT NULL,
                        deadline_type VARCHAR(50) NOT NULL,
                        deadline_date DATE NOT NULL,
                        requirements JSONB NOT NULL DEFAULT '{}',
                        status VARCHAR(50) DEFAULT 'pending',
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS timeline_milestones (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        due_date DATE NOT NULL,
                        category VARCHAR(50) NOT NULL,
                        priority VARCHAR(20) DEFAULT 'medium',
                        status VARCHAR(50) DEFAULT 'pending',
                        completion_date TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS deadline_reminders (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        deadline_id INTEGER REFERENCES application_deadlines(id),
                        reminder_date TIMESTAMP NOT NULL,
                        reminder_type VARCHAR(50) NOT NULL,
                        is_sent BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                self.conn.commit()
                logger.info("Database tables created/verified successfully")
        except psycopg2.Error as e:
            log_error(e, "Table creation")
            raise DatabaseError("Failed to initialize database tables")

    def execute(self, query, params=None):
        """Execute a query with automatic reconnection"""
        try:
            self._ensure_connection()
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params or ())
                if query.strip().upper().startswith('SELECT'):
                    return cur.fetchall()
                else:
                    self.conn.commit()
                    return []
        except psycopg2.Error as e:
            log_error(e, f"Query execution: {query}")
            raise DatabaseError("Database operation failed")

    def execute_one(self, query, params=None):
        """Execute a query and return a single result with automatic reconnection"""
        try:
            self._ensure_connection()
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params or ())
                result = cur.fetchone()
                if not query.strip().upper().startswith('SELECT'):
                    self.conn.commit()
                return result
        except psycopg2.Error as e:
            log_error(e, f"Query execution (single): {query}")
            raise DatabaseError("Database operation failed")