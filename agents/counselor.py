import logging
from openai import OpenAI
from utils.error_handling import AppError, log_error
import time

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

    def _make_api_call(self, messages, temperature=0.7):
        """Make OpenAI API call with retry mechanism"""
        retry_count = 0
        while retry_count < self.MAX_RETRIES:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=temperature
                )
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
            # Include relevant context in the prompt
            context_str = ""
            if context and context.get("profile"):
                profile = context["profile"]
                context_str = f"""
                Student Profile:
                - GPA: {profile.get('gpa', 'Not provided')}
                - Interests: {', '.join(profile.get('interests', []))}
                - Activities: {', '.join(profile.get('activities', []))}
                - Target Majors: {', '.join(profile.get('target_majors', []))}
                """

            messages = [
                {"role": "system", "content": self.system_prompt}
            ]

            if context_str:
                messages.append({"role": "system", "content": context_str})

            messages.append({"role": "user", "content": message})

            response = self._make_api_call(messages)
            logger.info("Successfully generated counselor response")
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise APIError("Unable to generate response. Please try again later.")

    def generate_college_list(self, profile):
        """Generate personalized college recommendations."""
        try:
            logger.info("Generating college recommendations")
            prompt = f"""
            Based on the following student profile, suggest 5-7 colleges that would be good fits:

            Profile:
            - GPA: {profile.get('gpa', 'Not provided')}
            - Interests: {', '.join(profile.get('interests', []))}
            - Activities: {', '.join(profile.get('activities', []))}
            - Target Majors: {', '.join(profile.get('target_majors', []))}

            For each college, please provide:
            1. Why it's a good academic fit
            2. Notable programs matching the student's interests
            3. Relevant extracurricular opportunities
            4. Approximate acceptance rate and middle 50% GPA range
            """
            return self._make_api_call([{"role": "user", "content": prompt}])
        except Exception as e:
            logger.error(f"Error generating college list: {str(e)}")
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

            Please provide actionable recommendations for:
            1. Academic improvements
            2. Extracurricular activities
            3. Test preparation
            4. Personal projects or initiatives
            """
            return self._make_api_call([{"role": "user", "content": prompt}], temperature=0.8)
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {str(e)}")
            raise APIError("Unable to generate improvement suggestions. Please try again later.")