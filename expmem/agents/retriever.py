"""
This class implements a retriever agent in DSPy that will retriever the right context, 
code, analysis, and debugging for the provided coding problem.

Initial version: Retrieve matching top k coding contexts from the database.


"""

#TODO: To few-shot or not?


import dspy

SYSTEM_PROMPT = """


You are an assistant that breaks down a problem and extracts keywords, concepts, and asks important questions.

Given a coding problem, identify main topics, concepts, and keywords relevant to solving it. Use these elements to formulate three targeted questions that clarify the core objectives, necessary techniques, and potential challenges.

Step-by-Step Instructions:
Identify Key Elements

Main Topics: The general area or type of task (e.g., sorting, searching, data manipulation).
Concepts: Specific programming concepts involved (e.g., recursion, dynamic programming, arrays).
Keywords: Essential terms, constraints, or parameters (e.g., threshold, precision, index, boundary).
Formulate Questions

Use the extracted topics, concepts, and keywords to create questions in these categories:
a. Core Objective Question

Purpose: Define the function’s main goal.
Example: "What is the function [function name] designed to achieve regarding [main topic]?"
b. Key Techniques, keywords or Methods Question

Purpose: Identify algorithms or data structures used.
Example: "Which [concepts] or techniques are essential to approach this [main topic]?"

c. Edge Cases or Errors Question

Purpose: Anticipate specific challenges or pitfalls.
Example: "What potential issues or errors might arise due to [list of keywords related to the coding problem]?"


"""

import os
from dotenv import load_dotenv

load_dotenv()

def get_model_openai(model: str, max_tokens: int = 2048, 
                     temperature: float = 0, top_p: float = 0.95,
                     system_prompt: str = None):
    
    return dspy.OpenAI(model=model, 
                       max_tokens=max_tokens, 
                       api_key=os.getenv("OPENAI_API_KEY"),
                       temperature=temperature, #Deterministic
                       system_prompt=system_prompt,
                       top_p=top_p) 

class ModularQuestions(dspy.Signature):
    """For the coding question, extract relevant topics, identify the main goal, and address potetial errors.
    Return the questions marked by Q1, Q2, etc.,"""
    
    coding_problem = dspy.InputField(desc='The coding problem to analyze')
    topics = dspy.OutputField(desc='List of main topics in the coding problem')
    keywords = dspy.OutputField(desc='The extracted keywords from the coding problem')
    questions = dspy.OutputField(desc='The extracted topics, main goal, and potential errors in question form')
    
    
class ModularQuestionsAgent(dspy.Module):
    def __init__(self, model_name="gpt-4o-mini-2024-07-18"):
        super().__init__()
        
        self.model = get_model_openai(model_name, system_prompt=SYSTEM_PROMPT)
        dspy.settings.configure(lm=self.model)
        
        self.extract_questions = dspy.Predict(ModularQuestions)
    
    def forward(self, coding_problem):
        prediction = self.extract_questions(coding_problem=coding_problem)
        
        return dspy.Prediction(questions=prediction.questions, 
                               keywords=prediction.keywords,
                               topics=prediction.topics)


def parse_questions(questions_str: str) -> list:
    # Split by Q1:, Q2:, etc. and clean up
    questions = questions_str.strip().split('\n')
    return [q.split(': ')[1].strip() for q in questions if q.strip()]

def parse_keywords(keywords_str: str) -> list:
   
    # Split by newline and remove dash prefix
    keywords = keywords_str.strip().split('\n')
    return [k.strip('- ') for k in keywords if k.strip()]

def parse_topics(topics_str: str) -> list:
    
    # Find the Topics: section
    if 'Topics:' in topics_str:
        
        topics_section = topics_str.split('Topics:')[1]
        
        # Split by newline and remove dash prefix
        topics = topics_section.strip().split('\n')
        
        return [t.strip('- ') for t in topics if t.strip()]
    
    return []

if __name__ == '__main__':
    mod_ques = ModularQuestionsAgent()
    
    from expmem.datasets.DatasetFactory import DatasetFactory
    dataset = DatasetFactory("HumanEval").get_dataset()
    data = dataset[0]
    
    coding_problem = data.prompt
    
    res = mod_ques(coding_problem)
    
    questions = parse_questions(res.questions)
    keywords = parse_keywords(res.keywords)
    topics = parse_topics(res.topics)
    
    print(f"Questions: {questions}")
    print(f"Keywords: {keywords}")
    print(f"Topics: {topics}")
    