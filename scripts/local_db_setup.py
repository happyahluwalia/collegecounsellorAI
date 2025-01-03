import os
from pathlib import Path

def create_env_template():
    """Create a template .env file with database connection details."""
    env_template = """# Database Configuration
# Replace these values with your Replit PostgreSQL credentials
DATABASE_URL=postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}
PGUSER=your_username
PGPASSWORD=your_password
PGHOST=your_host
PGPORT=your_port
PGDATABASE=your_database
"""
    
    # Create .env.example file
    with open('.env.example', 'w') as f:
        f.write(env_template)
    
    print("Created .env.example template file")
    print("1. Copy .env.example to .env")
    print("2. Replace the placeholder values with your Replit PostgreSQL credentials")
    print("3. Keep .env file secure and never commit it to version control")

if __name__ == "__main__":
    create_env_template()
