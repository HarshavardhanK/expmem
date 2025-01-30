
from expmem.database.PineconeRM import PineconeRetriever

import dspy
import os

from dspy.retrieve.pinecone_rm import PineconeRM

from dotenv import load_dotenv
load_dotenv()

def get_model_openai(model: str):

    model = dspy.OpenAI(model=model, 
                    max_tokens=500, 
                    api_key=os.getenv("OPENAI_API_KEY"))

    return model

class RAG(dspy.Module):
    def __init__(self, num_passages=2):
        super().__init__()

        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate_answer = dspy.ChainOfThought("question, context -> answer")

    def forward(self, question):
        context = self.retrieve(question).passages
        print('Context is: ', context)
        prediction = self.generate_answer(question=question, context=context)
        return dspy.Prediction(answer=prediction.answer, context=context)
    
class GenerateAnswer(dspy.Signature):

    """Answer the question by generating python code understanding the context with explanation.
        Return the answer 
        Explain your rationale after the answer as python comments.
        Only provide Python code enclosed in ``` ```"""
    
    context = dspy.InputField(desc="may contain relevant information")
    question = dspy.InputField()

    answer = dspy.OutputField(desc=f"often between 10 and 15 words")

from dsp.utils import deduplicate

class CustomQA(dspy.Module):
    def __init__(self, top_k=3):
        super().__init__()

        self.retrieve = dspy.Retrieve(k=top_k)
        self.generate_answer = dspy.Predict(GenerateAnswer)
        print(self.generate_answer)

    def forward(self, question):
        context = self.retrieve(question).passages
        prediction = self.generate_answer(context=context, question=question, number='3')

        return dspy.Prediction(answer=prediction.answer, context=context)
    

def trial_rag():

    pinecone = PineconeRetriever(pinecone_api=os.getenv("PINECONE_API_KEY"),
                                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                                    openai_embed_model="text-embedding-3-small",
                                    pinecone_index_name="example",
                                    pinecone_namespace="demo",
                                    dimension=1536,
                                    metric="cosine",
                                    top_k=3)
    
    model = get_model_openai("gpt-4o-mini-2024-07-18")

    # pinecone_rm = PineconeRM(pinecone_api_key=os.getenv("PINECONE_API_KEY"),
    #                          pinecone_index_name="example",
    #                          openai_embed_model="text-embedding-3-small",
    #                          openai_api_key=os.getenv("OPENAI_API_KEY"),
    #                          k=3)
                            

    dspy.settings.configure(lm=model, rm=pinecone)
    rag = CustomQA()
    res = rag("does harsha work in the city where he stays?")

    model.inspect_history(n=3)

    print('Result is: ', res)

from llm_sandbox import SandboxSession

def exec_code(code: str):

    import re

    def extract_python_code(text):
        pattern = r'(?s)```python\n(.*?)```'
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return None
    
    code = extract_python_code(code)

    try:
        return exec("hehehe")
    
    except Exception as e:
        print(e)
        return f"Encountered exception {e} while running code {code}"
    

    # with SandboxSession(lang="python", keep_template=True) as session:
    #     result = session.run(code)
    #     print(result.text)

def trial_code_generation():
    from expmem.database.PineconeClient import PineconeClient

    pc = PineconeClient(index_name="example", 
                        namespace="demo", 
                        dimension=1536, 
                        metric="cosine")
    
    # text = ["this is ananya she stays in munich, germany and she is from mangalore india",
    #         "ananya likes going to the beach and she loves to dance",
    #         "ananya is a neuroscience research scientist and she works at Neuralink",
    #         "ananya only likes cable cars to go on top of mountains, not trekking",
    #         "this is harsha he stays in riverside, ca and he is from udupi india",
    #         "harsha likes going to the beach and he loves to play cricket",
    #         "harsha is a software engineer and he works at google",
    #         "harsha likes trekking"]
    
    # pc.insert_context(context=text, chunk_size=1024, chunk_overlap=32)


    model = get_model_openai("gpt-4o-mini-2024-07-18")

    pinecone = PineconeRetriever(pinecone_api=os.getenv("PINECONE_API_KEY"),
                                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                                    openai_embed_model="text-embedding-3-small",
                                    pinecone_index_name="example",
                                    pinecone_namespace="demo",
                                    dimension=1536,
                                    metric="cosine",
                                    top_k=6)
                            

    dspy.settings.configure(lm=model, rm=pinecone)
    ret = dspy.Retrieve(k=6)

    
    rag = CustomQA(top_k=6)

    print("Asking the bot")
    question = "can harsha and ananya go on a trek together?"
    res = rag(question)
    #res1 = rag("Does harsha like trekking?")
    answer = res.answer
    print('Answer is: ', answer)
    ans = exec_code(answer)    

    pc.insert_context(context=f"Code Output for Question '{question}' = '{ans}'", chunk_size=1024, chunk_overlap=32)

    res = rag("what's one thing thats False about Harsha and Ananya?")

    print(res)


def trial_pc_client():
    from expmem.database.PineconeClient import PineconeClient

    pc = PineconeClient(index_name="example", 
                        namespace="demo", 
                        dimension=1536, 
                        metric="cosine")
    
    # text = ["this is ananya she stays in munich, germany and she is from mangalore india",
    #         "ananya likes going to the beach and she loves to dance",
    #         "ananya is a neuroscience research scientist and she works at Neuralink",
    #         "ananya only likes cable cars to go on top of mountains, not trekking",
    #         "this is harsha he stays in riverside, ca and he is from udupi india",
    #         "harsha likes going to the beach and he loves to play cricket",
    #         "harsha is a software engineer and he works at google",
    #         "harsha likes trekking"]
    
    # pc.insert_context(context=text, chunk_size=1024, chunk_overlap=32)


    model = get_model_openai("gpt-4o-mini-2024-07-18")

    pinecone = PineconeRetriever(pinecone_api=os.getenv("PINECONE_API_KEY"),
                                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                                    openai_embed_model="text-embedding-3-small",
                                    pinecone_index_name="example",
                                    pinecone_namespace="demo",
                                    dimension=1536,
                                    metric="cosine",
                                    top_k=6)
                            

    dspy.settings.configure(lm=model, rm=pinecone)
    ret = dspy.Retrieve(k=6)

    
    rag = CustomQA(top_k=6)

    print("Asking the bot")
    res = rag("can harsha and ananya go on a trek together?")
    #res1 = rag("Does harsha like trekking?")
    answer = res.answer
    print('Answer is: ', answer)    

    pc.insert_context(context=answer, chunk_size=1024, chunk_overlap=32)

    res = rag("what's the given rationale in context as to why harsha and ananya cannot do one activity together?")

    print(res)


if __name__ == '__main__':
    trial_code_generation()




