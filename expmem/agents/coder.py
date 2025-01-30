import dspy
import os
from dotenv import load_dotenv
import ast
import sys
from io import StringIO
import traceback
import pydantic
from typing import List

from expmem.datasets.DatasetFactory import DatasetFactory
from expmem.agents.debugger import CodeExecutorAgent
from expmem.agents.utils import execute_sample_ios, execute_test_case
from expmem.experiments.utils import extract_python_code
from expmem.database.PineconeRM import PineconeRetriever

load_dotenv()


def get_model_openai(model: str):
    return dspy.OpenAI(model=model, 
                       max_tokens=2048, 
                       api_key=os.getenv("OPENAI_API_KEY"),
                       temperature=0, #Deterministic
                       top_p=0.95) 


class GenerateCodeSimple(dspy.Signature):
    """Given the coding problem, generate Python code to solve the mentioned problem."""
    question = dspy.InputField(desc='The coding problem')
    code = dspy.OutputField(desc='The generated Python code')

class CodeGeneratorSimple(dspy.Module):
    def __init__(self, model_name="gpt-4o-mini-2024-07-18"):
        super().__init__()
        
        self.model = get_model_openai(model_name)
        dspy.settings.configure(lm=self.model)
        
        self.generate_code = dspy.Predict(GenerateCodeSimple)

    def forward(self, question):
        prediction = self.generate_code(question=question)
        
        return dspy.Prediction(code=prediction.code)
    

class GenerateCode(dspy.Signature):
    """Fill in Python code block to answer the given coding question.
    Provide a detailed explanation of the code even as comments for each line.
    Provide a detailed explanation of the code solution.
    Provide a summary explanation of the approach taken to solve the problem."""
    
    question = dspy.InputField(desc='contains the coding problem')
    code = dspy.OutputField(desc='The generated code solution')
    
    detailed_explanation = dspy.OutputField(desc='Detailed explanation of the code solution')
    summary_explanation = dspy.OutputField(desc='Summary explanation of the code solution')
    
    #code_response: CodeResponses = dspy.OutputField(desc='A list of code solutions with detailed and summary explanations. <IMPORTANT> This must follow a comma separated list of values </IMPORTANT>')

class CodeGenerator(dspy.Module):
    def __init__(self, model_name="gpt-4o-mini-2024-07-18"):
        super().__init__()
        
        self.model = get_model_openai(model_name)
        dspy.settings.configure(lm=self.model)
        
        self.generate_code = dspy.Predict(GenerateCode)

    def forward(self, question):
        prediction = self.generate_code(question=question)
        
        return dspy.Prediction(code=prediction.code, 
                               detailed=prediction.detailed_explanation,
                               summary=prediction.summary_explanation)
    

class CodeGeneratorMemory(dspy.Signature):
    """
    
    Fill in Python code block to answer the given coding question.
    You will be provided with context information which may contain similar problems with code solution,
    explanations about the problem and solution, and error analysis if any.
    
    You need to analyze the give context, understand similar problems and solutions given, and avoid the errors.
    
    Fill in the Python code block.
    
    """
    
    context = dspy.InputField(desc='contains the coding problem context of similar problems')
    question = dspy.InputField(desc='contains the coding problem to solve')
    
    code = dspy.OutputField(desc='The generated code solution')



class CodeExecutorAgentMemory(dspy.Module):
    
    def __init__(self, retriever, model_name="gpt-4o-mini-2024-07-18", top_k=6):
        super().__init__()
        
        self.model = get_model_openai(model_name)
        dspy.settings.configure(lm=self.model)
        
        self.coder = dspy.Predict(CodeGeneratorMemory)
        
        dspy.settings.configure(lm=self.model, rm=retriever)
        self.retrieve = dspy.Retrieve(k=top_k) 

        self.passed_test_case = False
        self.context = None
        
    def forward(self, prompt, test_case, entry_point):
        
        self.context = self.retrieve(prompt).passages
        
        print('Retrieved context is: ', self.context)
        
        gen_code = self.coder(context=self.context, question=prompt)
        
        code = gen_code.code
        
        if code is None:
            print("Code not generated")
            return dspy.Prediction(code=None)
        
        code = extract_python_code(code)
        
        if code is None:
            print("Code not generated")
            return dspy.Prediction(code=None)
        
        passed_test_case, _, _, full_code_test = execute_test_case(code, test_case, entry_point)
        
        return {
                'prediction': code,
                'context': self.context,
                "full_code_io": None,
                "full_code": full_code_test,
                "result": passed_test_case
                }

