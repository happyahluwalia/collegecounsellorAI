from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class ValidatorAgent:
    def __init__(self):
        self.llm = ChatOpenAI()
        self.system_prompt = """
        You are a fact-checking assistant for college admissions advice. 
        Verify that the advice is accurate and constructive. Flag any 
        potentially misleading or incorrect information.
        """

    def validate_response(self, message):
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", f"Please validate this college admissions advice: {message}")
        ])
        
        chain = prompt | self.llm
        result = chain.invoke({"input": message})
        return result.content

    def validate_college_list(self, colleges, student_profile):
        prompt = f"""
        Verify these college recommendations for the following student profile:
        Profile:
        {student_profile}
        
        Recommendations:
        {colleges}
        
        Are these recommendations appropriate? Please flag any concerns.
        """
        return self.get_response(prompt)
