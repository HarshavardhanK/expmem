
import os
from dotenv import load_dotenv

from expmem.agents.coder import GenerateCode, CodeGenerator, CodeExecutorAgentMemory
from expmem.agents.coder import CodeGeneratorSimple, GenerateCodeSimple
from expmem.agents.debugger import CodeExecutorAgent

from expmem.datasets.DatasetFactory import DatasetFactory

from expmem.experiments.utils import setup_csv, append_result, extract_python_code

from expmem.database.PineconeRM import PineconeRetriever

def simple_memory():
    
    load_dotenv()
    
    dataset = DatasetFactory('HumanEval').get_dataset()
    
    
    index = "expmem1"
    namespace = "expmem1"
    
    pinecone = PineconeRetriever(pinecone_api=os.getenv("PINECONE_API_KEY"),
                                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                                    openai_embed_model="text-embedding-3-small",
                                    pinecone_index_name=index,
                                    pinecone_namespace=namespace,
                                    dimension=1536,
                                    metric="cosine",
                                    top_k=6)
    
    code_gen = CodeExecutorAgentMemory(retriever=pinecone)
    
    result = []
    
    file = "humanEval_memory_naive4.csv"
    setup_csv(file)
    
    for data in dataset:
        #print('Prompt is: ', prompt)
        
        code_sol = code_gen(prompt=data.prompt, 
                            test_case=data.test, 
                            entry_point=data.entry_point)
        
        #code_gen.model.inspect_history(n=1)
        
        #print(code_sol)
        _ = append_result(filename=file, 
                          summary=None, 
                          detailed=None, 
                          data=data, 
                          ID=dataset._id, 
                          code=code_sol['prediction'], 
                          exec_res=code_sol)
        
        result.append(code_sol)
    
        # Print progress
        if code_sol['result']:
            print(f'Test cases passed for ID: {data[dataset._id]}')
            
    passed = [1 for r in result if r['result']]
    total_passed = sum(passed)
    print(f'Total test cases passed: {total_passed}, out of {len(dataset)}')

def trial_retrieval():
    
    load_dotenv()
    
    dataset = DatasetFactory('HumanEval').get_dataset()
    
    
    index = "expmem"
    namespace = "expmem"
    
    pinecone = PineconeRetriever(pinecone_api=os.getenv("PINECONE_API_KEY"),
                                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                                    openai_embed_model="text-embedding-3-small",
                                    pinecone_index_name=index,
                                    pinecone_namespace=namespace,
                                    dimension=1536,
                                    metric="cosine",
                                    top_k=6)
    
    code_gen = CodeExecutorAgentMemory(retriever=pinecone)
    
    data = dataset[0]
    
    code_sol = code_gen(prompt=data.prompt, 
                            test_case=data.test, 
                            entry_point=data.entry_point)
    
    
    print(code_sol)
 
 
def trial_contextual_memory():
    
    data = DatasetFactory('HumanEval')
    dataset = data.get_dataset()
    
    load_dotenv()
    
    index = "contextual"
    namespace = "contextual"
    
    pinecone = PineconeRetriever(pinecone_api=os.getenv("PINECONE_API_KEY"),
                                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                                    openai_embed_model="text-embedding-3-small",
                                    pinecone_index_name=index,
                                    pinecone_namespace=namespace,
                                    dimension=1536,
                                    metric="cosine",
                                    top_k=6)
    
    
    
    code_gen = CodeExecutorAgentMemory(retriever=pinecone)
    
    data = dataset[0]
    
    code_sol = code_gen(prompt=data.prompt, 
                            test_case=data.test, 
                            entry_point=data.entry_point)
    
    print(code_sol)
 
if __name__ == "__main__":
    simple_memory()
    #trial_retrieval()
    #trial_contextual_memory()