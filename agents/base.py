"""
Base agent implementation for the College Compass multi-agent system.
Provides common functionality and interfaces for specialized agents.
"""

import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI
import json
from utils.error_handling import AppError, log_error

logger = logging.getLogger(__name__)

class AgentError(AppError):
    """Agent-specific errors"""
    def __init__(self, message: str):
        super().__init__(message, "Agent Error")

class BaseAgent:
    """Base class for all specialized agents in the system"""

    def __init__(self, model: str = "gpt-4-turbo", temperature: float = 0.7):
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 1  # seconds
        self.system_prompt: str = ""  # Base system prompt to be overridden by subclasses

    def _make_api_call(self, messages: List[Dict[str, Any]], response_format: Optional[Dict[str, Any]] = None) -> str:
        """Make OpenAI API call with retry mechanism"""
        for attempt in range(self.MAX_RETRIES):
            try:
                completion_params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature
                }
                if response_format:
                    completion_params["response_format"] = response_format

                response = self.client.chat.completions.create(**completion_params)
                return response.choices[0].message.content

            except Exception as e:
                logger.warning(f"API call attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.MAX_RETRIES - 1:
                    log_error(e, "OpenAI API call")
                    raise AgentError(f"Failed to get response from {self.__class__.__name__}")

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