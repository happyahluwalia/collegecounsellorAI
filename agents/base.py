"""
Base agent implementation for the College Compass multi-agent system.
Provides common functionality and interfaces for specialized agents.
"""

import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI
from anthropic import Anthropic
import json
from utils.error_handling import AppError, log_error
from src.config.manager import ConfigManager, ModelConfig

logger = logging.getLogger(__name__)

class AgentError(AppError):
    """Agent-specific errors"""
    def __init__(self, message: str):
        super().__init__(message, "Agent Error")

class BaseAgent:
    """Base class for all specialized agents in the system"""

    def __init__(self, agent_type: str, config_manager: Optional[ConfigManager] = None):
        self.agent_type = agent_type
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_agent_config(agent_type)
        self.api_config = self.config_manager.get_model_api_config(self.config.provider)
        self.system_prompt = self.config_manager.get_prompt_template(agent_type)

        # Initialize primary and fallback clients
        self.primary_client = self._initialize_client(self.config.provider)
        self.fallback_client = None
        if self.config.fallback:
            self.fallback_client = self._initialize_client(
                self.config.fallback["provider"],
                is_fallback=True
            )

    def _initialize_client(self, provider: str, is_fallback: bool = False) -> Any:
        """Initialize API client based on provider"""
        try:
            if provider == "openai":
                return OpenAI(api_key=self.api_config["api_key"])
            elif provider == "anthropic":
                return Anthropic(api_key=self.api_config["api_key"])
            else:
                raise AgentError(f"Unsupported provider: {provider}")
        except Exception as e:
            if not is_fallback:
                logger.error(f"Error initializing {provider} client: {str(e)}")
                if self.fallback_client:
                    logger.info(f"Falling back to {self.config.fallback['provider']}")
                    return self.fallback_client
            raise AgentError(f"Failed to initialize {provider} client: {str(e)}")

    def _make_api_call(self, messages: List[Dict[str, Any]], response_format: Optional[Dict[str, Any]] = None) -> str:
        """Make API call with retry and fallback mechanism"""
        for attempt in range(self.api_config.get("retry_attempts", 3)):
            try:
                if self.config.provider == "openai":
                    return self._call_openai(messages, response_format)
                elif self.config.provider == "anthropic":
                    return self._call_anthropic(messages)

            except Exception as e:
                logger.warning(f"API call attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.api_config.get("retry_attempts", 3) - 1:
                    if self.fallback_client and self.config.fallback:
                        logger.info("Attempting fallback")
                        try:
                            # Switch to fallback configuration
                            original_config = self.config
                            self.config = ModelConfig(**self.config.fallback)
                            result = self._make_api_call(messages, response_format)
                            self.config = original_config
                            return result
                        except Exception as fallback_error:
                            logger.error(f"Fallback failed: {str(fallback_error)}")

                    log_error(e, "API call")
                    raise AgentError(f"Failed to get response from {self.__class__.__name__}")

    def _call_openai(self, messages: List[Dict[str, Any]], response_format: Optional[Dict[str, Any]] = None) -> str:
        """Make OpenAI API call"""
        completion_params = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": self.config.temperature
        }
        if self.config.max_tokens:
            completion_params["max_tokens"] = self.config.max_tokens
        if response_format:
            completion_params["response_format"] = response_format

        response = self.primary_client.chat.completions.create(**completion_params)
        return response.choices[0].message.content

    def _call_anthropic(self, messages: List[Dict[str, Any]]) -> str:
        """Make Anthropic API call"""
        # Convert messages to Anthropic format
        system_message = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_messages = [m["content"] for m in messages if m["role"] == "user"]

        message = self.primary_client.messages.create(
            model=self.config.model_name,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_message,
            messages=[{"role": "user", "content": msg} for msg in user_messages]
        )
        return message.content[0].text

    def get_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a response to the user's message with context"""
        try:
            logger.info(f"{self.__class__.__name__} generating response")
            messages = self._build_messages(message, context)
            response = self._make_api_call(messages)
            logger.info(f"{self.__class__.__name__} successfully generated response")
            return response

        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            raise AgentError(f"Failed to generate response in {self.__class__.__name__}")

    def _build_messages(self, message: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Build messages array for API call"""
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]
        if context:
            messages.append({
                "role": "system", 
                "content": f"Context: {json.dumps(context)}"
            })
        messages.append({"role": "user", "content": message})
        return messages

    def _build_context_string(self, context: Optional[Dict[str, Any]]) -> str:
        """Build context string from provided data"""
        if not context:
            return ""
        return json.dumps(context, indent=2)