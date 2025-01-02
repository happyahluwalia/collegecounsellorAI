"""
Agent Orchestrator implementation using LangGraph.
Manages communication and coordination between specialized agents.
"""

import logging
from typing import Dict, Any
from datetime import datetime # Added import
from langgraph.graph import Graph, MessageState
from .primary_counselor import PrimaryCounselorAgent
from .strategic_planning import StrategicPlanningAgent
from .base import AgentError
import json

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
    """Manages the multi-agent system using LangGraph"""
    
    def __init__(self):
        # Initialize agents
        self.agents = {
            "counselor": PrimaryCounselorAgent(),
            "strategic": StrategicPlanningAgent(),
            # Initialize other agents as they're implemented
        }
        
        # Initialize LangGraph
        self.graph = Graph()
        
        # Add nodes for each agent
        for agent_name, agent in self.agents.items():
            self.graph.add_node(agent_name, agent.process)
            
        # Define edges (agent communication paths)
        self._setup_communication_paths()

    def _setup_communication_paths(self):
        """Setup the communication paths between agents"""
        # Primary paths
        self.graph.add_edge("counselor", "strategic")
        # Add more edges as we implement other agents
        
    async def process_message(self, message: str, user_id: int) -> str:
        """Process a user message through the agent system"""
        try:
            # Initialize message state
            state = MessageState(
                messages=[],
                current_agent="counselor",
                user_id=user_id,
                original_message=message
            )
            
            # Get initial context
            context = await self.agents["counselor"].get_context(user_id)
            
            # Create initial agent message
            agent_message = AgentMessage(
                sender="user",
                content={"message": message},
                metadata={"context": context}
            )
            
            # Add message to state
            state.messages.append(agent_message.to_dict())
            
            # Process through graph
            final_state = await self.graph.arun(state)
            
            # Extract final response
            final_message = final_state.messages[-1]
            return final_message["content"]["response"]
            
        except Exception as e:
            logger.error(f"Error in message processing: {str(e)}")
            raise AgentError("Failed to process message through agent system")
            
    def add_agent(self, name: str, agent: Any):
        """Add a new agent to the system"""
        try:
            self.agents[name] = agent
            self.graph.add_node(name, agent.process)
            logger.info(f"Added new agent: {name}")
        except Exception as e:
            logger.error(f"Error adding agent {name}: {str(e)}")
            raise AgentError(f"Failed to add agent: {name}")
            
    def remove_agent(self, name: str):
        """Remove an agent from the system"""
        try:
            if name in self.agents:
                del self.agents[name]
                self.graph.remove_node(name)
                logger.info(f"Removed agent: {name}")
        except Exception as e:
            logger.error(f"Error removing agent {name}: {str(e)}")
            raise AgentError(f"Failed to remove agent: {name}")
            
    def get_agent_status(self) -> Dict:
        """Get status of all agents in the system"""
        return {
            name: "active" for name in self.agents.keys()
        }

# Example usage of the orchestrator:
"""
orchestrator = AgentOrchestrator()

# Process a user message
response = await orchestrator.process_message(
    "I need help planning my college applications",
    user_id=123
)

# Add a new agent
new_agent = EssayDevelopmentAgent()
orchestrator.add_agent("essay", new_agent)

# Get system status
status = orchestrator.get_agent_status()
"""