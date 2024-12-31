import os
import psycopg2
from psycopg2.extras import RealDictCursor

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.conn = psycopg2.connect(
                host=os.environ['PGHOST'],
                database=os.environ['PGDATABASE'],
                user=os.environ['PGUSER'],
                password=os.environ['PGPASSWORD'],
                port=os.environ['PGPORT']
            )
            cls._instance.create_tables()
        return cls._instance

    def create_tables(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
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
            """)
            self.conn.commit()

    def execute(self, query, params=None):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            return cur.fetchall()

    def execute_one(self, query, params=None):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            return cur.fetchone()
