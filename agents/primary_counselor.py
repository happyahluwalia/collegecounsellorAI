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
        self.config = self._load_config()
        logger.info(f"Initialized {self.__class__.__name__} with config: {self.config}")

    def _load_config(self) -> Dict:
        """Load configuration from YAML template"""
        try:
            if hasattr(self, 'config_manager') and self.config_manager:
                logger.info(f"Loading template for agent type: {self.agent_type}")
                if not hasattr(self.config_manager, '_prompts') or not self.config_manager._prompts:
                    logger.error("No prompts found in config manager")
                    return self._get_default_config()

                templates = self.config_manager._prompts.get('templates', {})
                template = templates.get(self.agent_type, {})
                logger.info(f"Found template for {self.agent_type}: {template}")

                if not template or 'base_prompt' not in template:
                    logger.error(f"No valid template found for {self.agent_type}")
                    return self._get_default_config()

                config = {
                    'provider': 'openai',
                    'model_name': 'gpt-4-turbo-preview',
                    'temperature': 0.7,
                    'max_tokens': 2000,
                    'system_prompt_template': template['base_prompt'],
                    'fallback': {
                        'provider': 'anthropic',
                        'model_name': 'claude-3-sonnet'
                    }
                }
                logger.info(f"Loaded config with system prompt: {config['system_prompt_template']}")
                return config
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Return default configuration with fallback system prompt"""
        default_prompt = """You are a college admissions counselor. Provide guidance and advice to students.
        When providing recommendations, use the following format for actionable items:

        <actionable id="1">Specific action or recommendation here</actionable>

        At the end of your response, include:

        [system]
        actionable:
        [1]
        category: [Category]
        year: [Grade Level]
        url: [Optional URL]
        [/system]
        """
        return {
            'provider': 'openai',
            'model_name': 'gpt-4-turbo-preview',
            'temperature': 0.7,
            'max_tokens': 2000,
            'system_prompt_template': default_prompt,
            'fallback': {
                'provider': 'anthropic',
                'model_name': 'claude-3-sonnet'
            }
        }

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
                logger.warning("No system message found in response")
                return []

            # Parse system metadata
            system_content = system_match.group(1).strip()
            metadata = {}
            current_id = None
            current_metadata = {}

            for line in system_content.split('\n'):
                line = line.strip()
                if line:
                    if line.startswith('actionable:'):
                        continue
                    if line.startswith('[') and line.endswith(']'):
                        if current_id is not None and current_metadata:
                            metadata[current_id] = current_metadata
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

        # Format actionable items within the text
        for item in actionable_items:
            # Replace the basic actionable tag with formatted text
            display_response = display_response.replace(
                f'<actionable id="{item.item_id}">{item.text}</actionable>',
                f'{item.text}'  # Just keep the text, the UI will handle the formatting
            )

        # Clean up any remaining actionable tags (fallback)
        display_response = re.sub(r'<actionable id="\d+">(.*?)</actionable>', r'\1', display_response)

        # Clean up multiple newlines
        display_response = re.sub(r'\n{3,}', '\n\n', display_response)

        return {
            "content": display_response,
            "actionable_items": [item.to_dict() for item in actionable_items]
        }

    def _build_messages(self, message: str, context: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Build messages list for the API call including system prompt and context"""
        try:
            base_prompt = """You are a college admissions counselor. Provide guidance and advice to students.
            When providing recommendations, use the following format for actionable items:
            <actionable id="1">Specific action or recommendation here</actionable>

            For each actionable item, include a system message at the end of your response in this exact format:

            [system]
            actionable:
            [1]
            category: [Category of activity e.g. 'Summer Programs', 'Courses', etc.]
            year: [Grade year e.g. '9th', '10th', '11th', '12th']
            url: [Optional URL for more information]
            [/system]"""

            logger.info(f"Building messages with base prompt: {base_prompt}")
            messages = [
                {
                    "role": "system",
                    "content": base_prompt
                }
            ]

            # Add context if available
            if context:
                context_str = self._build_context_string(context)
                messages.append({
                    "role": "system",
                    "content": f"Additional context about the student:\n{context_str}"
                })

            # Add user message
            messages.append({
                "role": "user",
                "content": message
            })

            logger.info(f"Complete messages array: {messages}")
            return messages

        except Exception as e:
            logger.error(f"Error building messages: {str(e)}")
            raise AgentError("Failed to build messages")

    def _make_api_call(self, messages: List[Dict[str, str]]) -> str:
        """Make API call to LLM provider"""
        try:
            logger.info("Making API call with messages: %s", json.dumps(messages, indent=2))
            # Use the configured provider (OpenAI or Anthropic)
            provider = self.config.get('provider', 'openai')

            if provider == 'openai':
                if not hasattr(self, 'openai_client'):
                    from openai import OpenAI
                    self.openai_client = OpenAI()

                response = self.openai_client.chat.completions.create(
                    model=self.config.get('model_name', 'gpt-4-turbo-preview'),
                    messages=messages,
                    temperature=self.config.get('temperature', 0.7),
                    max_tokens=self.config.get('max_tokens', 2000)
                )
                result = response.choices[0].message.content
                logger.info(f"Raw OpenAI response: {result}")
            else:
                if not hasattr(self, 'anthropic_client'):
                    from anthropic import Anthropic
                    self.anthropic_client = Anthropic()

                response = self.anthropic_client.messages.create(
                    model=self.config.get('model_name', 'claude-3-opus'),
                    max_tokens=self.config.get('max_tokens', 4000),
                    temperature=self.config.get('temperature', 0.5),
                    messages=[
                        {"role": m["role"], "content": m["content"]} 
                        for m in messages
                    ]
                )
                result = response.content[0].text
                logger.info(f"Raw Anthropic response: {result}")

            # For debugging, save the system prompt and response in messages table
            if hasattr(self, 'db'):
                try:
                    self.db.execute(
                        """
                        INSERT INTO messages (session_id, content, role, metadata)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            -1,  # Use -1 as special session_id for debug messages
                            json.dumps({
                                'system_prompt': messages[0]['content'],
                                'raw_response': result
                            }),
                            'debug',
                            {'debug': True}
                        )
                    )
                except Exception as db_error:
                    logger.error(f"Failed to save debug message: {str(db_error)}")

            return result

        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            if self.config.get('fallback'):
                logger.info("Attempting fallback provider")
                old_config = self.config.copy()
                self.config = self.config['fallback']
                try:
                    result = self._make_api_call(messages)
                    logger.info("Fallback API call succeeded")
                    return result
                finally:
                    self.config = old_config
            raise AgentError(f"Failed to get response from LLM: {str(e)}")

    def get_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict:
        """Generate a response to the user's message with context and actionable items"""
        try:
            logger.info(f"{self.__class__.__name__} generating response")
            messages = self._build_messages(message, context)
            raw_response = self._make_api_call(messages)
            logger.info(f"Raw response received: {raw_response[:200]}...")  # Log first 200 chars

            # Parse actionable items
            actionable_items = self._parse_actionable_items(raw_response)
            logger.info(f"Found {len(actionable_items)} actionable items")

            # Format the response
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