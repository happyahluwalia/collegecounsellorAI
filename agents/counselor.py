from openai import OpenAI
import os

class CounselorAgent:
    def __init__(self):
        self.client = OpenAI()
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

    def get_response(self, message, context=None):
        """Generate a response to the user's message."""
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

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content

    def generate_college_list(self, profile):
        """Generate personalized college recommendations."""
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
        return self.get_response(prompt)

    def suggest_improvements(self, profile):
        """Suggest ways to improve college application."""
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
        return self.get_response(prompt)