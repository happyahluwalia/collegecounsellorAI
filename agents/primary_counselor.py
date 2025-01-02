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
    def __init__(self, item_id: str, text: str, category: str, year: str, url: Optional[str] = None):
        self.item_id = item_id
        self.text = text
        self.category = category
        self.year = year
        self.url = url

    def to_dict(self) -> Dict:
        return {
            "id": self.item_id,
            "text": self.text,
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

    def _parse_actionable_items(self, response: str) -> List[ActionableItem]:
        """Parse response to find actionable items and their details"""
        try:
            # Extract all actionable tags with their content
            actionable_pattern = r'<actionable id="([^"]+)">(.*?)</actionable>'
            actionable_matches = re.finditer(actionable_pattern, response, re.DOTALL)

            # Extract system message
            system_pattern = r'\[system\](.*?)\[/system\]'
            system_match = re.search(system_pattern, response, re.DOTALL)

            if not system_match:
                return []

            # Parse system metadata
            system_content = system_match.group(1).strip()
            metadata = {}
            current_id = None
            current_metadata = {}

            for line in system_content.split('\n'):
                line = line.strip()
                if line:
                    if line.startswith('[') and line.endswith(']'):
                        # If we have a previous item, save it
                        if current_id is not None and current_metadata:
                            metadata[current_id] = current_metadata
                        # Start new item
                        current_id = line[1:-1]
                        current_metadata = {}
                    elif ':' in line and current_id is not None:
                        key, value = line.split(':', 1)
                        current_metadata[key.strip().lower()] = value.strip()

            # Save the last item
            if current_id is not None and current_metadata:
                metadata[current_id] = current_metadata

            # Create ActionableItem objects
            actionable_items = []
            for match in actionable_matches:
                item_id = match.group(1)
                text = match.group(2).strip()
                if item_id in metadata:
                    item_meta = metadata[item_id]
                    actionable_items.append(
                        ActionableItem(
                            item_id=item_id,
                            text=text,
                            category=item_meta.get('category', ''),
                            year=item_meta.get('year', ''),
                            url=item_meta.get('url')
                        )
                    )

            return actionable_items

        except Exception as e:
            logger.error(f"Error parsing actionable items: {str(e)}")
            return []

    def _format_response_with_actionable(self, response: str, actionable_items: List[ActionableItem]) -> Dict:
        """Format the response by removing system message and actionable tags"""
        # Remove system message
        display_response = re.sub(r'\[system\].*?\[/system\]', '', response, flags=re.DOTALL).strip()

        # Remove actionable tags but keep the content
        for item in actionable_items:
            display_response = display_response.replace(
                f'<actionable id="{item.item_id}">{item.text}</actionable>',
                f'**{item.text}**'
            )

        return {
            "content": display_response,
            "actionable_items": [item.to_dict() for item in actionable_items]
        }

    def get_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict:
        """Generate a response to the user's message with context and actionable items"""
        try:
            logger.info(f"{self.__class__.__name__} generating response")
            messages = self._build_messages(message, context)
            raw_response = self._make_api_call(messages)

            # Parse actionable items
            actionable_items = self._parse_actionable_items(raw_response)
            formatted_response = self._format_response_with_actionable(raw_response, actionable_items)

            logger.info(f"{self.__class__.__name__} successfully generated response with actionable items")
            return formatted_response

        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            raise AgentError(f"Failed to generate response in {self.__class__.__name__}")

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