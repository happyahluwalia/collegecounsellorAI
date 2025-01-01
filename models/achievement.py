from typing import Dict, Optional, List
from datetime import datetime
from models.database import Database
from utils.error_handling import DatabaseError, ValidationError
import logging
import json
import traceback

logger = logging.getLogger(__name__)

class Achievement:
    def __init__(self, id=None, name=None, description=None, icon_name=None,
                 points=0, category=None, requirements=None):
        self.id = id
        self.name = name
        self.description = description
        self.icon_name = icon_name
        self.points = points
        self.category = category
        self.requirements = requirements or {}
        self.db = Database()

    @classmethod
    def initialize_default_achievements(cls):
        """Create default achievements if they don't exist."""
        try:
            # First, ensure the name column has a unique constraint
            db = Database()
            db.execute("""
                ALTER TABLE achievements 
                ADD CONSTRAINT unique_achievement_name UNIQUE (name)
            """)
            logger.info("Added unique constraint to achievements name column")
        except Exception as e:
            # Ignore if constraint already exists
            if "already exists" not in str(e):
                error_trace = traceback.format_exc()
                logger.error(f"Error adding unique constraint: {str(e)}\n{error_trace}")
                raise DatabaseError(f"Failed to initialize achievements table: {str(e)}")

        defaults = [
            {
                'name': 'Profile Pioneer',
                'description': 'Complete your student profile with all information',
                'icon_name': '👤',
                'points': 100,
                'category': 'profile',
                'requirements': json.dumps({
                    'profile_fields': ['gpa', 'interests', 'activities', 
                                   'target_majors', 'target_schools']
                })
            },
            {
                'name': 'Chat Champion',
                'description': 'Have 5 meaningful conversations with the AI counselor',
                'icon_name': '💬',
                'points': 150,
                'category': 'engagement',
                'requirements': json.dumps({
                    'chat_sessions': 5
                })
            },
            {
                'name': 'Goal Getter',
                'description': 'Set and track 3 college application goals',
                'icon_name': '🎯',
                'points': 200,
                'category': 'planning',
                'requirements': json.dumps({
                    'goals_set': 3
                })
            }
        ]

        try:
            for achievement in defaults:
                db.execute("""
                    INSERT INTO achievements 
                    (name, description, icon_name, points, category, requirements)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO NOTHING
                """, (
                    achievement['name'],
                    achievement['description'],
                    achievement['icon_name'],
                    achievement['points'],
                    achievement['category'],
                    achievement['requirements']
                ))
            logger.info("Default achievements initialized successfully")
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Error initializing default achievements: {str(e)}\n{error_trace}")
            raise DatabaseError(f"Failed to initialize default achievements: {str(e)}")

    @classmethod
    def get_all(cls) -> List['Achievement']:
        """Get all available achievements."""
        try:
            db = Database()
            results = db.execute("SELECT * FROM achievements ORDER BY category, points")
            return [cls(**result) for result in results]
        except Exception as e:
            logger.error(f"Error fetching achievements: {str(e)}")
            raise DatabaseError("Failed to fetch achievements")

    def check_progress(self, user_id: int, current_state: Dict) -> Optional[bool]:
        """Check if an achievement's requirements are met."""
        try:
            # Get current progress
            progress = self.db.execute_one("""
                SELECT progress, completed FROM user_achievements 
                WHERE user_id = %s AND achievement_id = %s
            """, (user_id, self.id))

            if not progress:
                # Initialize progress tracking
                self.db.execute("""
                    INSERT INTO user_achievements (user_id, achievement_id, progress)
                    VALUES (%s, %s, %s)
                """, (user_id, self.id, json.dumps(current_state)))
                return False

            if progress['completed']:
                return None  # Already completed

            # Check if requirements are met
            is_complete = self._evaluate_requirements(current_state)

            if is_complete:
                # Update achievement completion
                self.db.execute("""
                    UPDATE user_achievements 
                    SET completed = true, completed_at = CURRENT_TIMESTAMP,
                        progress = %s
                    WHERE user_id = %s AND achievement_id = %s
                """, (json.dumps(current_state), user_id, self.id))
                logger.info(f"User {user_id} completed achievement {self.name}")

            return is_complete

        except Exception as e:
            logger.error(f"Error checking achievement progress: {str(e)}")
            raise DatabaseError("Failed to check achievement progress")

    def _evaluate_requirements(self, current_state: Dict) -> bool:
        """Evaluate if the current state meets achievement requirements."""
        try:
            requirements = json.loads(self.requirements) if isinstance(self.requirements, str) else self.requirements

            for key, required_value in requirements.items():
                if key not in current_state:
                    return False

                current_value = current_state[key]

                if isinstance(required_value, (int, float)):
                    if current_value < required_value:
                        return False
                elif isinstance(required_value, list):
                    if not all(field in current_value for field in required_value):
                        return False

            return True
        except Exception as e:
            logger.error(f"Error evaluating requirements: {str(e)}")
            return False

    @classmethod
    def get_user_achievements(cls, user_id: int) -> List[Dict]:
        """Get all achievements and their progress for a user."""
        try:
            db = Database()
            results = db.execute("""
                SELECT a.*, ua.progress, ua.completed, ua.completed_at
                FROM achievements a
                LEFT JOIN user_achievements ua 
                    ON ua.achievement_id = a.id AND ua.user_id = %s
                ORDER BY a.category, a.points
            """, (user_id,))

            return results
        except Exception as e:
            logger.error(f"Error fetching user achievements: {str(e)}")
            raise DatabaseError("Failed to fetch user achievements")