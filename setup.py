import os
import sys
import logging
import subprocess
import time
import toml
from typing import Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SetupManager:
    def __init__(self):
        self.environment = self._detect_environment()

    def _detect_environment(self) -> str:
        """Detect if running on Replit or locally"""
        return 'replit' if os.environ.get('REPL_ID') else 'local'

    def check_database_config(self) -> bool:
        """Verify database configuration exists"""
        try:
            # For local setup, check if .env exists
            if self.environment == 'local':
                if not os.path.exists('.env'):
                    logger.info("Creating .env from template...")
                    if os.path.exists('.env.example'):
                        with open('.env.example', 'r') as example_file:
                            with open('.env', 'w') as config_file:
                                config_file.write(example_file.read())
                        logger.info("Created .env file. Please update with your database credentials.")
                        return True
                    else:
                        logger.error(".env.example not found")
                        return False
            return True
        except Exception as e:
            logger.error(f"Error checking database config: {str(e)}")
            return False

    def setup_database(self) -> bool:
        """Set up the database schema and import initial data"""
        try:
            logger.info("Setting up database...")

            # Import college data using the restructured import
            from data.importers.college_data_importer import CollegeDataImporter
            importer = CollegeDataImporter(
                os.path.join('data', 'All_college_export.csv')
            )
            importer.import_all()

            logger.info("Database setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            return False

    def verify_dependencies(self) -> bool:
        """Verify all required packages are installed"""
        try:
            logger.info("Verifying project dependencies...")

            # Install toml first if not available
            try:
                import toml
            except ImportError:
                logger.info("Installing toml package...")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "toml"
                ])

            # Read dependencies from pyproject.toml
            with open('pyproject.toml', 'r') as f:
                project_config = toml.load(f)

            dependencies = project_config.get('project', {}).get('dependencies', [])

            # Filter out version specifiers to get just package names
            required_packages = [
                pkg.split('>=')[0].strip() 
                for pkg in dependencies
            ]

            logger.info(f"Required packages: {', '.join(required_packages)}")

            # Use pip to install missing packages
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    *required_packages
                ])
                logger.info("All dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install dependencies: {str(e)}")
                return False

            logger.info("All dependencies verified")
            return True
        except Exception as e:
            logger.error(f"Dependency verification failed: {str(e)}")
            return False

    def start_application(self) -> bool:
        """Start the Streamlit application"""
        try:
            logger.info("Starting application...")
            os.makedirs('.streamlit', exist_ok=True)

            # Create Streamlit config if it doesn't exist
            config_path = '.streamlit/config.toml'
            if not os.path.exists(config_path):
                with open(config_path, 'w') as f:
                    f.write("""
[server]
headless = true
address = "0.0.0.0"
port = 5000
                    """.strip())

            # Start the application
            if self.environment == 'local':
                logger.info("Starting Streamlit locally...")
                subprocess.run([sys.executable, "-m", "streamlit", "run", "main.py"])
            else:
                subprocess.Popen([sys.executable, "-m", "streamlit", "run", "main.py"])

            logger.info("Application started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start application: {str(e)}")
            return False

    def run_setup(self) -> bool:
        """Run the complete setup process"""
        steps = [
            ("Checking database configuration", self.check_database_config),
            ("Verifying dependencies", self.verify_dependencies),
            ("Setting up database", self.setup_database),
            ("Starting application", self.start_application)
        ]

        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            if not step_func():
                logger.error(f"Setup failed at step: {step_name}")
                return False
            logger.info(f"Completed: {step_name}")

        logger.info("Setup completed successfully!")
        return True

if __name__ == "__main__":
    setup = SetupManager()
    setup.run_setup()