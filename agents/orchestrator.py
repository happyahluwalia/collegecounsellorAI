"""
Agent Orchestrator implementation using LangGraph.
Manages communication and coordination between specialized agents.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from .primary_counselor import PrimaryCounselorAgent
from .strategic_planning import StrategicPlanningAgent
from .base import AgentError
from src.config.manager import ConfigManager
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

class AgentMessage:
    """Message format for inter-agent communication"""
    def __init__(self, sender: str, content: Dict[str, Any], metadata: Dict[str, Any] = None):
        self.sender = sender
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }

class AgentOrchestrator:
    """Manages the multi-agent system"""

    def __init__(self):
        try:
            # Initialize configuration manager
            self.config_manager = ConfigManager()

            # Initialize agents with configuration
            self.agents = {
                "counselor": PrimaryCounselorAgent(
                    agent_type="primary_counselor",
                    config_manager=self.config_manager
                ),
                "strategic": StrategicPlanningAgent(
                    agent_type="strategic_planning",
                    config_manager=self.config_manager
                ),
            }

            logger.info("Successfully initialized AgentOrchestrator with all agents")
        except Exception as e:
            logger.error(f"Failed to initialize AgentOrchestrator: {str(e)}")
            raise AgentError(f"Failed to initialize agent system: {str(e)}")

    async def process_message(self, message: str, user_id: Optional[int] = None) -> str:
        """Process a user message through the agent system"""
        try:
            logger.info(f"Processing message for user {user_id}: {message[:100]}...")

            # Get initial context from primary counselor
            context = {}
            if user_id:
                try:
                    context = await self.agents["counselor"].get_context(user_id)
                    logger.info("Successfully retrieved user context")
                except Exception as e:
                    logger.warning(f"Failed to get user context: {str(e)}")
                    # Continue without context rather than failing

            # First, let the primary counselor analyze the query
            try:
                routing = self.agents["counselor"].route_query(message, context)
                logger.info(f"Query routing decision: {routing}")
            except Exception as e:
                logger.error(f"Failed to route query: {str(e)}")
                routing = {"needs_routing": False}

            # Route to appropriate agent based on analysis
            try:
                if routing.get("needs_routing") and routing.get("target_agent") in self.agents:
                    response = self.agents[routing["target_agent"]].get_response(message, context)
                    logger.info(f"Got response from {routing['target_agent']} agent")
                else:
                    # Default to primary counselor
                    response = self.agents["counselor"].get_response(message, context)
                    logger.info("Got response from primary counselor")

                return response

            except Exception as e:
                logger.error(f"Failed to get agent response: {str(e)}")
                raise AgentError("Unable to generate response. Please try again.")

        except Exception as e:
            logger.error(f"Error in message processing: {str(e)}")
            raise AgentError(str(e))

    def get_agent_status(self) -> Dict[str, str]:
        """Get status of all agents in the system"""
        return {
            name: "active" for name in self.agents.keys()
        }

    def get_agent_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get current configuration of all agents"""
        return {
            name: agent.config.dict() 
            for name, agent in self.agents.items()
        }