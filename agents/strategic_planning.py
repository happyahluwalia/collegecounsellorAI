"""
Strategic Planning Agent (SPA) implementation.
This agent handles long-term planning and strategy development for college applications.
"""

from typing import Dict, Optional, List
import logging
from .base import BaseAgent, AgentError
from models.database import Database
from src.config.manager import ConfigManager
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class StrategicPlanningAgent(BaseAgent):
    """Handles long-term planning and strategy development for college applications"""

    def __init__(self, agent_type: str = "strategic_planning", config_manager: Optional[ConfigManager] = None):
        super().__init__(agent_type=agent_type, config_manager=config_manager)
        self.db = Database()
        logger.info(f"Initialized {self.__class__.__name__} with config: {self.config}")

    async def analyze_profile(self, user_id: int) -> Dict:
        """Analyze student profile and current progress"""
        try:
            profile = self.db.execute_one(
                "SELECT * FROM profiles WHERE user_id = %s",
                (user_id,)
            )

            deadlines = self.db.execute(
                "SELECT * FROM application_deadlines WHERE user_id = %s",
                (user_id,)
            )

            milestones = self.db.execute(
                "SELECT * FROM timeline_milestones WHERE user_id = %s",
                (user_id,)
            )

            return {
                "profile": profile,
                "deadlines": deadlines,
                "milestones": milestones
            }

        except Exception as e:
            logger.error(f"Error analyzing profile: {str(e)}")
            raise AgentError("Failed to analyze profile")

    def generate_strategy(self, profile_data: Dict) -> str:
        """Generate a comprehensive application strategy"""
        try:
            prompt = f"""
            Create a detailed college application strategy based on this profile:
            {json.dumps(profile_data, indent=2)}

            Respond in JSON format with:
            {{
                "immediate_actions": [string],
                "short_term_goals": [string],
                "long_term_goals": [string],
                "profile_gaps": [string],
                "recommended_timeline": {{
                    "next_30_days": [string],
                    "next_90_days": [string],
                    "next_6_months": [string],
                    "next_year": [string]
                }},
                "test_prep_strategy": {{
                    "recommended_tests": [string],
                    "preparation_timeline": string,
                    "study_recommendations": [string]
                }}
            }}
            """

            response = self._make_api_call(
                [{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            return response

        except Exception as e:
            logger.error(f"Error generating strategy: {str(e)}")
            raise AgentError("Failed to generate application strategy")

    def identify_profile_gaps(self, profile_data: Dict) -> List[Dict]:
        """Identify gaps in student profile and suggest improvements"""
        try:
            prompt = f"""
            Analyze this student profile and identify areas needing improvement:
            {json.dumps(profile_data, indent=2)}

            Respond in JSON format with:
            {{
                "gaps": [
                    {{
                        "area": string,
                        "current_status": string,
                        "target_status": string,
                        "improvement_actions": [string],
                        "priority": "high" | "medium" | "low",
                        "timeline": string
                    }}
                ]
            }}
            """

            response = self._make_api_call(
                [{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            gaps = json.loads(response)["gaps"]
            return gaps

        except Exception as e:
            logger.error(f"Error identifying profile gaps: {str(e)}")
            return []

    def generate_milestone_recommendations(self, profile_data: Dict) -> List[Dict]:
        """Generate recommended milestones based on profile and goals"""
        try:
            current_date = datetime.now()

            prompt = f"""
            Create a list of recommended milestones for this student:
            {json.dumps(profile_data, indent=2)}

            Current date: {current_date.isoformat()}

            Respond in JSON format with:
            {{
                "milestones": [
                    {{
                        "title": string,
                        "description": string,
                        "due_date": string (YYYY-MM-DD),
                        "category": string,
                        "priority": "high" | "medium" | "low"
                    }}
                ]
            }}
            """

            response = self._make_api_call(
                [{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            milestones = json.loads(response)["milestones"]
            return milestones

        except Exception as e:
            logger.error(f"Error generating milestone recommendations: {str(e)}")
            return []

    def adjust_strategy(self, current_strategy: Dict, progress_data: Dict) -> Dict:
        """Adjust strategy based on student's progress"""
        try:
            prompt = f"""
            Adjust this strategy based on current progress:

            Current Strategy:
            {json.dumps(current_strategy, indent=2)}

            Progress Data:
            {json.dumps(progress_data, indent=2)}

            Provide updated strategy in the same JSON format as the current strategy.
            """

            response = self._make_api_call(
                [{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            updated_strategy = json.loads(response)
            return updated_strategy

        except Exception as e:
            logger.error(f"Error adjusting strategy: {str(e)}")
            raise AgentError("Failed to adjust strategy")