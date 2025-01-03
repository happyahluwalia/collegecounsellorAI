import os
import yaml
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the configuration manager"""
        self.config = {}
        self.environment = self._detect_environment()
        self._load_config()
    
    def _detect_environment(self) -> str:
        """Detect the current environment"""
        if os.environ.get('REPL_ID'):
            return 'replit'
        return os.environ.get('APP_ENV', 'local')
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'database.yaml')
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
                logger.info(f"Loaded configuration for environment: {self.environment}")
            else:
                logger.warning(f"Configuration file not found at {config_path}")
                self.config = {}
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            self.config = {}
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration for the current environment"""
        try:
            # Get environment specific config with fallback to default
            env_config = self.config.get(self.environment, {})
            default_config = self.config.get('default', {})
            
            # If in Replit environment and use_env_vars is True, use environment variables
            if self.environment == 'replit' and env_config.get('use_env_vars', False):
                return {
                    'host': os.environ.get('PGHOST'),
                    'port': os.environ.get('PGPORT'),
                    'database': os.environ.get('PGDATABASE'),
                    'user': os.environ.get('PGUSER'),
                    'password': os.environ.get('PGPASSWORD')
                }
            
            # Merge default config with environment specific config
            config = {**default_config, **env_config}
            
            # Remove special keys
            config.pop('use_env_vars', None)
            config.pop('fallback', None)
            
            return config
        except Exception as e:
            logger.error(f"Error getting database configuration: {str(e)}")
            return {}
    
    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """Get the singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
