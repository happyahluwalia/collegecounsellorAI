import os
import sys
import logging
from typing import Optional
import subprocess
import time

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
            if not os.path.exists('config/database.yaml'):
                logger.info("Creating database.yaml from example...")
                if os.path.exists('config/database.yaml.example'):
                    with open('config/database.yaml.example', 'r') as example_file:
                        with open('config/database.yaml', 'w') as config_file:
                            config_file.write(example_file.read())
                    logger.info("Database configuration created successfully")
                    return True
                else:
                    logger.error("database.yaml.example not found")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking database config: {str(e)}")
            return False

    def setup_database(self) -> bool:
        """Set up the database schema and import initial data"""
        try:
            logger.info("Setting up database...")
            
            # Import college data
            import data.import.college_data_importer
            importer = data.import.college_data_importer.CollegeDataImporter(
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
        required_packages = [
            'streamlit',
            'langchain',
            'openai',
            'anthropic',
            'psycopg2-binary',
            'pyyaml',
            'pandas',
            'plotly'
        ]
        
        try:
            import pkg_resources
            installed_packages = [pkg.key for pkg in pkg_resources.working_set]
            
            missing_packages = [pkg for pkg in required_packages if pkg not in installed_packages]
            
            if missing_packages:
                logger.info(f"Installing missing packages: {', '.join(missing_packages)}")
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            
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
            
            # Start the application using subprocess
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
