from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.chat_models.openai import ChatOpenAI
from langgraph.graph import END, Graph

class CounselorAgent:
    def __init__(self):
        self.llm = ChatOpenAI()
        self.system_prompt = """
        You are an experienced college admissions counselor helping high school students 
        with their college applications. Be encouraging and supportive while providing 
        specific, actionable advice. Focus on helping students discover their interests 
        and find colleges that match their profile.
        """

    def create_workflow(self):
        workflow = Graph()

        @workflow.node()
        def process_input(message):
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("human", "{input}")
            ])
            chain = prompt | self.llm
            response = chain.invoke({"input": message})
            return {"response": response.content, "next": "validate"}

        @workflow.node()
        def validate(message):
            # Add validation logic here
            return {"response": message["response"], "next": END}

        workflow.set_entry_point("process_input")
        workflow.add_edge("process_input", "validate")

        return workflow

    def get_response(self, message, context=None):
        workflow = self.create_workflow()
        result = workflow.invoke(message)
        return result["response"]

    def generate_college_list(self, profile):
        prompt = f"""
        Based on the following student profile, suggest 5-7 colleges that would be good fits:
        GPA: {profile.get('gpa')}
        Interests: {', '.join(profile.get('interests', []))}
        Activities: {', '.join(profile.get('activities', []))}
        Target Majors: {', '.join(profile.get('target_majors', []))}

        For each college, explain why it would be a good fit.
        """
        return self.get_response(prompt)