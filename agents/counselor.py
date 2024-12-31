import logging
from openai import OpenAI
from utils.error_handling import AppError, log_error
import time
import json

logger = logging.getLogger(__name__)

class APIError(AppError):
    """OpenAI API related errors"""
    def __init__(self, message: str):
        super().__init__(message, "API Error")

class CounselorAgent:
    def __init__(self):
        self.client = OpenAI()
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 1  # seconds
        self.system_prompt = """
        You are an experienced college admissions counselor with expertise in guiding high school students 
        through their college application journey. Your role is to:

        1. Provide personalized guidance based on the student's academic profile, interests, and goals
        2. Help students explore and identify suitable college majors
        3. Suggest colleges that match their profile and aspirations
        4. Offer strategic advice for improving their application
        5. Answer questions about the college application process
        6. Provide emotional support and encouragement

        Be encouraging, specific, and actionable in your advice. Focus on helping students discover 
        their strengths and find colleges where they can thrive.
        """

    def _make_api_call(self, messages, temperature=0.7, response_format=None):
        """Make OpenAI API call with retry mechanism"""
        retry_count = 0
        while retry_count < self.MAX_RETRIES:
            try:
                completion_params = {
                    "model": "gpt-3.5-turbo",
                    "messages": messages,
                    "temperature": temperature
                }
                if response_format:
                    completion_params["response_format"] = response_format

                response = self.client.chat.completions.create(**completion_params)
                return response.choices[0].message.content
            except Exception as e:
                retry_count += 1
                logger.warning(f"API call attempt {retry_count} failed: {str(e)}")
                if retry_count >= self.MAX_RETRIES:
                    log_error(e, "OpenAI API call")
                    raise APIError("Unable to get response from AI counselor. Please try again later.")
                time.sleep(self.RETRY_DELAY * retry_count)  # Exponential backoff

    def get_response(self, message, context=None):
        """Generate a response to the user's message."""
        try:
            logger.info("Generating counselor response")
            context_str = self._build_context_string(context)
            messages = self._build_messages(message, context_str)
            response = self._make_api_call(messages)
            logger.info("Successfully generated counselor response")
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise APIError("Unable to generate response. Please try again later.")

    def _build_context_string(self, context):
        """Build context string from user profile"""
        if not context or not context.get("profile"):
            return ""

        profile = context["profile"]
        return f"""
        Student Profile:
        - GPA: {profile.get('gpa', 'Not provided')}
        - Interests: {', '.join(profile.get('interests', []))}
        - Activities: {', '.join(profile.get('activities', []))}
        - Target Majors: {', '.join(profile.get('target_majors', []))}
        """

    def _build_messages(self, message, context_str=""):
        """Build messages array for API call"""
        messages = [{"role": "system", "content": self.system_prompt}]
        if context_str:
            messages.append({"role": "system", "content": context_str})
        messages.append({"role": "user", "content": message})
        return messages

    def generate_college_matches(self, profile, limit=10):
        """Generate personalized college recommendations with detailed matching criteria."""
        try:
            logger.info("Generating personalized college matches")
            prompt = f"""
            Based on this student's profile, recommend {limit} best-fit colleges. 
            Provide a structured analysis in JSON format with the following schema:
            {{
                "colleges": [
                    {{
                        "name": "College Name",
                        "match_score": float (0-1),
                        "academic_fit": string,
                        "program_strengths": [strings],
                        "extracurricular_matches": [strings],
                        "admission_stats": {{
                            "acceptance_rate": float,
                            "gpa_range": {{
                                "min": float,
                                "max": float
                            }}
                        }},
                        "why_good_fit": string
                    }}
                ]
            }}

            Student Profile:
            - GPA: {profile.get('gpa', 'Not provided')}
            - Interests: {', '.join(profile.get('interests', []))}
            - Activities: {', '.join(profile.get('activities', []))}
            - Target Majors: {', '.join(profile.get('target_majors', []))}
            """

            response = self._make_api_call(
                [{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            # Validate and serialize the response
            recommendations = json.loads(response)
            recommendations_json = json.dumps(recommendations)
            logger.info(f"Generated {len(recommendations.get('colleges', []))} college matches")
            return recommendations_json  # Return JSON string instead of dict

        except Exception as e:
            logger.error(f"Error generating college matches: {str(e)}")
            raise APIError("Unable to generate college recommendations. Please try again later.")

    def suggest_improvements(self, profile):
        """Suggest ways to improve college application."""
        try:
            logger.info("Generating improvement suggestions")
            prompt = f"""
            Based on this student's profile, suggest specific ways they can strengthen their college application:

            Current Profile:
            - GPA: {profile.get('gpa', 'Not provided')}
            - Interests: {', '.join(profile.get('interests', []))}
            - Activities: {', '.join(profile.get('activities', []))}
            - Target Majors: {', '.join(profile.get('target_majors', []))}

            Provide recommendations in JSON format:
            {{
                "academic_improvements": [string],
                "extracurricular_suggestions": [string],
                "test_prep_recommendations": [string],
                "personal_projects": [string],
                "priority_level": string
            }}
            """
            return self._make_api_call(
                [{"role": "user", "content": prompt}],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {str(e)}")
            raise APIError("Unable to generate improvement suggestions. Please try again later.")