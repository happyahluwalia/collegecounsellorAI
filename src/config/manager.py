"""
Configuration manager for the College Compass LLM system.
Handles loading and managing configurations for different LLM providers and agents.
"""

from pathlib import Path
from typing import Optional, Dict, Any, Union
import yaml
import os
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    """Configuration model for LLM agents"""
    provider: str
    model_name: str
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    max_tokens: Optional[int] = None
    system_prompt_template: str
    fallback: Optional[Dict[str, Any]] = None

class ConfigManager:
    """Manages loading and accessing configurations for the LLM system"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.env = os.getenv("APP_ENV", "development")
        self._config = self._load_config()
        self._prompts = self._load_prompts()

    def _load_config(self) -> Dict[str, Any]:
        """Load the main configuration file"""
        with open(self.config_dir / "models.yaml") as f:
            config = yaml.safe_load(f)
        return self._resolve_env_vars(config["environments"][self.env])

    def _load_prompts(self) -> Dict[str, Any]:
        """Load the prompts configuration file"""
        with open(self.config_dir / "prompts.yaml") as f:
            return yaml.safe_load(f)

    def _resolve_env_vars(self, config: Union[str, Dict, list, Any]) -> Union[str, Dict, list, Any]:
        """Resolve environment variables in config values"""
        if isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]
            return os.getenv(env_var, "")
        elif isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(v) for v in config]
        return config

    def get_agent_config(self, agent_type: str) -> ModelConfig:
        """Get configuration for specific agent"""
        config_dict = self._config["agents"].get(agent_type)
        if not config_dict:
            raise ValueError(f"No configuration found for agent type: {agent_type}")
        return ModelConfig(**config_dict)

    def get_model_api_config(self, provider: str) -> Dict[str, Any]:
        """Get API configuration for specific provider"""
        return self._config["models"].get(provider, {})

    def get_prompt_template(self, template_name: str) -> str:
        """Get prompt template by name"""
        return self._prompts["templates"].get(template_name, {}).get("base_prompt", "")