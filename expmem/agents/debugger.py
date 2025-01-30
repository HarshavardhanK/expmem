
import dspy
import os
from dotenv import load_dotenv
import ast
import sys
from io import StringIO
import traceback

from expmem.datasets.DatasetFactory import DatasetFactory

load_dotenv()

import pydantic
from typing import List

from expmem.agents.utils import execute_sample_ios, execute_test_case


# Analyze and store the Sample IO

def get_model_openai(model: str):
    return dspy.OpenAI(model=model, 
                       max_tokens=2048, 
                       api_key=os.getenv("OPENAI_API_KEY"))


class DebugAndAnalyze(dspy.Signature):
    
    """You will be provided with a programming problem context, its solution, sample test cases, and results of execution of those sample test cases.
        Your task is to debug the code, if any bugs mentioned in the errors, and analyze the execution results.
        If there is any Exception or Error, explain the reason and provide an analysis.
        If there is no Exception or Error, provide an analysis of the code execution."""
    
    programming_context = dspy.InputField(desc='contains the coding problem.')
    code = dspy.InputField(desc="python code solution for the coding problem.")

    sample_io = dspy.InputField(desc="sample test cases for the code solution.")

    execution_result = dspy.InputField(desc="Result of code execution")
    execution_error = dspy.InputField(desc="Error occurred during code execution")

    error_analysis = dspy.OutputField(desc="Analysis of the code execution")
    

class CodeExecutorAgent(dspy.Module):
    def __init__(self, model_name="gpt-4o-mini-2024-07-18"):
        super().__init__()
        
        self.model = get_model_openai(model_name)
        dspy.settings.configure(lm=self.model)
        
        self.execute_and_analyze = dspy.Predict(DebugAndAnalyze)

        self.passed_test_case = False

    def forward(self, prompt, code, sample_ios, tests, entry_point):

        print("Calling Code execute")
        
        #Execute Sample IO and get feedback / store res
        _, result_io, error_io, full_code_io = execute_sample_ios(code, sample_ios) 
        
        #Execute test case and return the result
        passed_test_case, _, _, full_code_test = execute_test_case(code, tests, entry_point)
        
        sample_ios_ = "\n".join(sample_ios)
        execution_result_str = "\n".join(result_io)
        error_str = "\n".join(error_io)
        
        # Analyze the execution result and generate test cases
        prediction = self.execute_and_analyze(
            programming_context=prompt,
            code=code,
            sample_io=sample_ios_,

            execution_result=execution_result_str,
            execution_error=error_str
        )
        
        return {
                'prediction': dspy.Prediction(analysis=prediction.error_analysis),
                "full_code_io": full_code_io,
                "full_code": full_code_test,
                "result": passed_test_case
                }

    

