import dspy
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
    

"""
This class is responsible for giving contexting to chunks.
It will take in the Document D, and give chunks a context.

Document: {(Prompt, Code Solution) - whole document,
            (Prompt, Summary Explanation) - whole document,
            (Prompt, Detailed Explanation) - Contextually chunked,
            (Prompt, Error Analysis)} - Contextually chunked
            

1. Summrize and clean the prompt before.

"""

class ContextProvider(dspy.Signature):
    
    """Analyze this sentence within the coding document. Be precise and technical. I need to understand:

    Which document section it belongs to (code solution, summary, detailed explanation, or error analysis)
    If you find code description, provide a clean pseudo-code snippet for context.
    Its technical relationship to surrounding content. 
    What is the previous context and the next context?
    Its specific purpose in the document.
    
    Please give a short succinct context to situate this sentence within the overall document for the purposes of improving search retrieval of the sentence. 
    Answer only with the succinct context and nothing else."""
        
    sentence = dspy.InputField(desc='The sentence to be analyzed')
    document = dspy.InputField(desc='The document containing context about the sentence')
        
    prev_context = dspy.OutputField(desc='Summary of the previous context')
    next_context = dspy.OutputField(desc='Summary of the next context')
    purpose = dspy.OutputField(desc='The purpose of the sentence in the document')
        
class ContextualChunker(dspy.Module):
    
    def __init__(self, model_name="gpt-4o-mini-2024-07-18"):
        super().__init__()
        
        self.system_prompt = """You are a code documentation analyzer. 
                                Given a sentence from a coding document and the full document, 
                                identify how that sentence fits within the technical explanation. 
                                Focus on its relationship to code implementation, context explanation, and error cases. 
                                Provide only essential technical context in a brief format."""
                                
        self.model = get_model_openai(model=model_name, system_prompt=self.system_prompt)
        dspy.settings.configure(lm=self.model)
        
        self.context_provider = dspy.Predict(ContextProvider)
        
    def forward(self, sentence, document):
        
        if isinstance(document, dict):
            document = str(document)
            
        prediction = self.context_provider(sentence=sentence, document=document)
        
        return dspy.Prediction(prev_context=prediction.prev_context, 
                               next_context=prediction.next_context, 
                               purpose=prediction.purpose)
    
    


# TRIAL SECTION
from langchain.text_splitter import TokenTextSplitter

def trial():
    
    from langchain_core.documents import Document
    
    cont = ContextualChunker()
    
    sentence = """6. **Calculating Differences**: Inside the loop, we calculate the difference between the current element and the next element.
                  7. **Checking the Threshold**: If the calculated difference is less than the specified `threshold`, we immediately return `True`, indicating that we found at least one pair of close elements."""
    
    
    
    import pandas as pd
    
    df = pd.read_csv("humanEval_results_detail2.csv")
    data = df.iloc[0]
    
    data['Prompt'] = "from typing import List\n\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    \"\"\" Check if in given list of numbers, are any two numbers closer to each other than\n    given threshold.\n    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n    True\n    \"\"\"\n"
    document = {}
    document['solution'] = (data['Prompt'], data['Code']) #document [0]
    document['summary_exp'] = (data['Summary Explanation']) #document [1]
        
    #To be chunked
    document['detailed_exp'] = (data['Detailed Explanation']) #document [2]
    document['error_analysis'] = (data['Error Analysis']) #document [3]
    
    #print('-------------- Document is: ', document['detailed_exp'])
    
    splitter = TokenTextSplitter(
        encoding_name="cl100k_base", chunk_size=128, chunk_overlap=16
    )
    
    document_ = Document(page_content=document['detailed_exp'], 
                        metadata={"title": "Detailed Explanation"})
    #print('----->>', document_)
    docs = splitter.split_documents([document_])
    
    
    for doc in docs:
        print('Chunk is: ', doc.page_content)
        res = cont(doc.page_content, document)
        print(res)
        print("--------------------------------------")
    
    # print("--------- RES -----------------")
    # print(res)
        

if __name__ == '__main__':
    trial()
    