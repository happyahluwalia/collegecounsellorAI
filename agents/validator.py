import os
from openai import OpenAI

class ValidatorAgent:
    def __init__(self):
        self.client = OpenAI()
        self.system_prompt = """
        You are a fact-checking assistant for college admissions advice. 
        Verify that the advice is accurate and constructive. Flag any 
        potentially misleading or incorrect information.
        """

    def validate_response(self, message):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Please validate this college admissions advice: {message}"}
            ]
        )
        return response.choices[0].message.content

    def validate_college_list(self, colleges, student_profile):
        prompt = f"""
        Verify these college recommendations for the following student profile:
        Profile:
        {student_profile}

        Recommendations:
        {colleges}

        Are these recommendations appropriate? Please flag any concerns.
        """
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content