import dspy
import os
from dotenv import load_dotenv
import ast
import sys
from io import StringIO
import traceback

load_dotenv()

def get_model_openai(model: str):
    return dspy.OpenAI(model=model, 
                       max_tokens=2048, 
                       api_key=os.getenv("OPENAI_API_KEY"))

class GenerateCode(dspy.Signature):
    """Generate Python code to answer the given coding question.
    Provide a detailed explanation of the code as comments."""
    
    question = dspy.InputField(desc='contains the coding problem')
    
    code = dspy.OutputField(desc="Python code answering the question")

class CodeGenerator(dspy.Module):
    def __init__(self, model_name="gpt-4o-mini-2024-07-18", top_k=3):
        super().__init__()
        
        self.model = get_model_openai(model_name)
        dspy.settings.configure(lm=self.model)
        
        self.generate_code = dspy.Predict(GenerateCode)

    def forward(self, question):
        prediction = self.generate_code(question=question)
        
        return dspy.Prediction(code=prediction.code)

def sample_code_generator():
    code_gen = CodeGenerator()
    
    question = "Write a Python function to calculate the fibonacci sequence up to n terms."
    result = code_gen(question)
    
    print(f"Question: {question}\n")
    print(f"Generated Code:\n{result.code}\n")

class ExecuteAndAnalyze(dspy.Signature):
    """Execute the given Python code, analyze its output, create test cases, and report results."""
    
    code = dspy.InputField(desc="Python code to execute and analyze")
    
    execution_result = dspy.OutputField(desc="Result of code execution")
    analysis = dspy.OutputField(desc="Analysis of the code execution")
    test_cases = dspy.OutputField(desc="Generated test cases using assert statements")
    error_report = dspy.OutputField(desc="Detailed error report if any exceptions occurred")

class CodeExecutorAgent(dspy.Module):
    def __init__(self, model_name="gpt-4o-mini-2024-07-18"):
        super().__init__()
        
        self.model = get_model_openai(model_name)
        dspy.settings.configure(lm=self.model)
        
        self.execute_and_analyze = dspy.Predict(ExecuteAndAnalyze)

    def forward(self, code):
        # Execute the code
        execution_result, error = self._execute_code(code)
        
        # Analyze the execution result and generate test cases
        prediction = self.execute_and_analyze(
            code=code,
        )
        
        return dspy.Prediction(
            execution_result=prediction.execution_result,
            analysis=prediction.analysis,
            test_cases=prediction.test_cases,
            error_report=prediction.error_report
        )

    def _execute_code(self, code):
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        result = ""
        error = ""

        try:
            # Execute the code
            exec(code, globals())
            result = sys.stdout.getvalue()
        except Exception as e:
            error = f"Exception: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        finally:
            # Restore stdout
            sys.stdout = old_stdout

        return result, error


def sample_code_executor():
    code_executor = CodeExecutorAgent()
    
    # Sample code (Fibonacci sequence generator from previous example)
    code = """
def fibonacci(n):
    fib_sequence = []
    if n <= 0:
        return fib_sequence
    elif n == 1:
        fib_sequence.append(0)
        return fib_sequence
    elif n == 2:
        fib_sequence.extend([0, 1])
        return fib_sequence
    fib_sequence.extend([0, 1])
    for i in range(2, n):
        next_term = fib_sequence[i - 1] + fib_sequence[i - 2]
        fib_sequence.append(next_term)
    return fib_sequence

# Example usage:
n_terms = 10
print(fibonacci(n_terms))
"""

    result = code_executor(code)
    
    print("Execution Result:")
    print(result.execution_result)
    print("\nAnalysis:")
    print(result.analysis)
    print("\nTest Cases:")
    print(result.test_cases)
    print("\nError Report:")
    print(result.error_report)

def test_contextual_memory():
    

if __name__ == "__main__":
    sample_code_executor()