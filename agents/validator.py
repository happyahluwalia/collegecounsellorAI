import os
import logging
import time
from openai import OpenAI
from utils.error_handling import AppError, log_error

logger = logging.getLogger(__name__)

class ValidationError(AppError):
    """Validation related errors"""
    def __init__(self, message: str):
        super().__init__(message, "Validation Error")

class ValidatorAgent:
    def __init__(self):
        self.client = OpenAI()
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 1  # seconds
        self.system_prompt = """
        You are a fact-checking assistant for college admissions advice. 
        Verify that the advice is accurate and constructive. Flag any 
        potentially misleading or incorrect information.
        """

    def _make_api_call(self, messages):
        """Make OpenAI API call with retry mechanism"""
        retry_count = 0
        while retry_count < self.MAX_RETRIES:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages
                )
                return response.choices[0].message.content
            except Exception as e:
                retry_count += 1
                logger.warning(f"Validation API call attempt {retry_count} failed: {str(e)}")
                if retry_count >= self.MAX_RETRIES:
                    log_error(e, "OpenAI Validation API call")
                    raise ValidationError("Unable to validate response. Proceeding with caution.")
                time.sleep(self.RETRY_DELAY * retry_count)  # Exponential backoff

    def validate_response(self, message):
        try:
            logger.info("Validating counselor response")
            response = self._make_api_call([
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Please validate this college admissions advice: {message}"}
            ])
            logger.info("Successfully validated response")
            return response
        except Exception as e:
            logger.error(f"Error validating response: {str(e)}")
            # Return original message if validation fails
            logger.warning("Returning original message due to validation failure")
            return message

    def validate_college_list(self, colleges, student_profile):
        try:
            logger.info("Validating college recommendations")
            prompt = f"""
            Verify these college recommendations for the following student profile:
            Profile:
            {student_profile}

            Recommendations:
            {colleges}

            Are these recommendations appropriate? Please flag any concerns.
            """
            response = self._make_api_call([
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ])
            logger.info("Successfully validated college recommendations")
            return response
        except Exception as e:
            logger.error(f"Error validating college list: {str(e)}")
            raise ValidationError("Unable to validate college recommendations. Please review carefully.")