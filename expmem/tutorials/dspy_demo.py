import os

from dotenv import load_dotenv
load_dotenv()

import dspy
from dspy.teleprompt import BootstrapFewShot
from dspy.evaluate import Evaluate
from dspy.datasets.gsm8k import GSM8K, gsm8k_metric

from dspy.predict.avatar import Avatar, Tool

class CoT(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought("question -> answer")

    def forward(self, question):
        return self.prog(question = question)

def get_model_openai(model: str):

    model = dspy.OpenAI(model=model, 
                    max_tokens=500, 
                    api_key=os.getenv("OPENAI_API_KEY"))

    return model

def gsm8k_example():
    model = get_model_openai("gpt-4o-mini-2024-07-18")
    dspy.settings.configure(lm=model)

    gsm8k = GSM8K()
    gsm8k_trainset, gsm8k_devset = gsm8k.train[:10], gsm8k.dev[:10]

    print(gsm8k_trainset)
    


    config = dict(max_bootstrapped_demos=4, max_labeled_demos=4)
    teleprompter = BootstrapFewShot(metric=gsm8k_metric, **config)
    optimized_cot = teleprompter.compile(CoT(), trainset=gsm8k_trainset)



    evaluate = Evaluate(devset=gsm8k_devset, 
                        metric=gsm8k_metric, 
                        num_threads=4, 
                        display_progress=True, 
                        display_table=0)

    evaluate(optimized_cot)

    model.inspect_history(n = 1)


# ReAct Example
class BasicQA(dspy.Signature):
    """Answer questions with short factoid answers"""
    question = dspy.InputField()
    answer = dspy.OutputField(desc="often between 1 and 5 words")

def react_example():

    model = get_model_openai("gpt-4o-mini-2024-07-18")
    dspy.settings.configure(lm=model)

    react_module = dspy.ReAct(BasicQA)

    #Take input from the user from the command line
    question = input("Enter a question: ")
    result = react_module(question=question)

    print(result)

    model.inspect_history(n = 3)


""" An RAG Example """

class GenerateAnswer(dspy.Signature):
    """Answer questions with short factoid answers"""

    context = dspy.InputField(desc="may contain relevant facts")
    question = dspy.InputField()
    answer = dspy.OutputField(desc="often between 1 and 5 words")

class RAG(dspy.Module):
    def __init__(self, num_passages=3):
        super().__init__()

        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate_answer = dspy.ChainOfThought(GenerateAnswer)

    def forward(self, question):
        context = get_context(question)
        prediction = self.generate_answer(question=question, context=context)

        return dspy.Prediction(context=context, answer=prediction.answer)

if __name__ == "__main__":
    #gsm8k_example()
    react_example()
    