"""
Primary Counselor Agent (PCA) implementation.
This agent serves as the main interface for student interaction and conversation management.
"""

from typing import Dict, Optional, List
import logging
from .base import BaseAgent, AgentError
from models.database import Database
import json

logger = logging.getLogger(__name__)

class PrimaryCounselorAgent(BaseAgent):
    def __init__(self):
        super().__init__(model="gpt-4-turbo", temperature=0.7)
        self.system_prompt = """
        You are an experienced college admissions counselor with expertise in guiding high school 
        students through their college application journey. Your role is to:

        1. Maintain engaging, personalized conversations
        2. Route complex queries to specialized agents
        3. Maintain conversation context and student profile awareness
        4. Generate natural, empathetic responses
        5. Help students explore and identify suitable college majors
        6. Suggest colleges that match their profile and aspirations
        7. Provide emotional support and encouragement

        Always be encouraging, specific, and actionable in your advice. Focus on helping students 
        discover their strengths and find colleges where they can thrive.
        """
        self.db = Database()

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

    def route_query(self, query: str, context: Dict) -> str:
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