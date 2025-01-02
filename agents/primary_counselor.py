"""
Primary Counselor Agent (PCA) implementation.
This agent serves as the main interface for student interaction and conversation management.
"""

from typing import Dict, Optional, List, Any
import logging
import re
from .base import BaseAgent, AgentError
from models.database import Database
from src.config.manager import ConfigManager
import json

logger = logging.getLogger(__name__)

class ActionableItem:
    """Represents an actionable item detected in the agent's response"""
    def __init__(self, category: str, year: str, url: Optional[str] = None):
        self.category = category
        self.year = year
        self.url = url

    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "year": self.year,
            "url": self.url
        }

class PrimaryCounselorAgent(BaseAgent):
    """Primary counselor agent that manages main student interactions"""

    def __init__(self, agent_type: str = "primary_counselor", config_manager: Optional[ConfigManager] = None):
        super().__init__(agent_type=agent_type, config_manager=config_manager)
        self.db = Database()
        logger.info(f"Initialized {self.__class__.__name__} with config: {self.config}")

    def _parse_system_message(self, response: str) -> Optional[ActionableItem]:
        """Parse system message to extract actionable item details"""
        try:
            system_pattern = r'\[system\](.*?)\[/system\]'
            match = re.search(system_pattern, response, re.DOTALL)

            if match:
                system_content = match.group(1).strip()
                # Parse key-value pairs
                pairs = {}
                for line in system_content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        pairs[key.strip().lower()] = value.strip()

                return ActionableItem(
                    category=pairs.get('category', ''),
                    year=pairs.get('year', ''),
                    url=pairs.get('url')
                )
            return None
        except Exception as e:
            logger.error(f"Error parsing system message: {str(e)}")
            return None

    def _format_response_with_actionable(self, response: str, actionable_item: Optional[ActionableItem]) -> Dict:
        """Format the response with actionable item if present"""
        # Remove system message from displayed response
        display_response = re.sub(r'\[system\].*?\[/system\]', '', response, flags=re.DOTALL).strip()

        return {
            "content": display_response,
            "actionable_item": actionable_item.to_dict() if actionable_item else None
        }

    async def get_context(self, user_id: int) -> Dict:
        """Fetch relevant user context from database"""
        try:
            profile = self.db.execute_one(
                "SELECT * FROM profiles WHERE user_id = %s", 
                (user_id,)
            )

            recent_messages = self.db.execute(
                """SELECT content, role 
                FROM messages m 
                JOIN chat_sessions cs ON m.session_id = cs.id 
                WHERE cs.user_id = %s 
                ORDER BY m.created_at DESC LIMIT 10""",
                (user_id,)
            )

            achievements = self.db.execute(
                "SELECT * FROM user_achievements WHERE user_id = %s",
                (user_id,)
            )

            return {
                "profile": profile,
                "recent_messages": recent_messages,
                "achievements": achievements
            }

        except Exception as e:
            logger.error(f"Error fetching context: {str(e)}")
            raise AgentError("Failed to fetch user context")

    def route_query(self, query: str, context: Dict) -> Dict:
        """Determine if query should be routed to a specialized agent"""
        try:
            routing_prompt = f"""
            Analyze this query and determine if it should be handled by a specialized agent.
            Query: {query}

            Available specialized agents:
            1. Strategic Planning Agent: Long-term planning and strategy
            2. Timeline Management Agent: Deadlines and schedules
            3. College Research Agent: College matching and research
            4. Activity Planning Agent: Extracurricular planning
            5. Essay Development Agent: Essay guidance

            Respond in JSON format:
            {{
                "needs_routing": boolean,
                "target_agent": string or null,
                "reason": string
            }}
            """

            response = self._make_api_call(
                [{"role": "user", "content": routing_prompt}],
                response_format={"type": "json_object"}
            )

            routing_decision = json.loads(response)
            logger.info(f"Routing decision: {routing_decision}")
            return routing_decision

        except Exception as e:
            logger.error(f"Error in query routing: {str(e)}")
            return {"needs_routing": False, "target_agent": None, "reason": "Routing failed"}

    def get_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict:
        """Generate a response to the user's message with context and actionable items"""
        try:
            logger.info(f"{self.__class__.__name__} generating response")
            messages = self._build_messages(message, context)
            raw_response = self._make_api_call(messages)

            # Parse actionable items
            actionable_item = self._parse_system_message(raw_response)
            formatted_response = self._format_response_with_actionable(raw_response, actionable_item)

            logger.info(f"{self.__class__.__name__} successfully generated response with actionable items")
            return formatted_response

        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            raise AgentError(f"Failed to generate response in {self.__class__.__name__}")

    def generate_followup_questions(self, context: Dict) -> List[str]:
        """Generate relevant follow-up questions based on context"""
        try:
            prompt = f"""
            Based on the student's profile and conversation history, generate 3 relevant 
            follow-up questions to gather more information or provide better guidance.

            Current Context:
            {self._build_context_string(context)}

            Respond in JSON format:
            {{
                "questions": [
                    string,
                    string,
                    string
                ]
            }}
            """

            response = self._make_api_call(
                [{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            questions = json.loads(response)["questions"]
            return questions

        except Exception as e:
            logger.error(f"Error generating follow-up questions: {str(e)}")
            return []

    def summarize_session(self, session_messages: List[Dict]) -> str:
        """Generate a summary of the counseling session"""
        try:
            messages_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in session_messages
            ])

            prompt = f"""
            Summarize this counseling session, highlighting:
            1. Key topics discussed
            2. Advice given
            3. Action items for the student
            4. Areas needing follow-up

            Session transcript:
            {messages_text}
            """

            summary = self._make_api_call([{"role": "user", "content": prompt}])
            return summary

        except Exception as e:
            logger.error(f"Error summarizing session: {str(e)}")
            return "Session summary unavailable"