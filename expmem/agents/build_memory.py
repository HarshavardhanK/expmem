"""
How to go on about building 'memory' for the agent?

Do we pick random samples from the dataset run and store as context? How effective is random?
Do we categorize the samples and pick exemplar from each category?
Do we pick samples that are hard to solve?

1. Do we pair prompt context with other attributes like code, summary explanation, detailed explanation, error analysis??
2. Annotate each attribute and retrieve all for a document?

1. For the initial version choose random 25% of the dataset and store as context
    Chunk them with chunk size 1024 and chunk overlap of 32.

"""

from typing import Optional, List

def read_ids_from_file(filepath: str) -> List[str]:
    """Read and return list of IDs from a text file."""
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r') as f:
        return [line.strip() for line in f.readlines()]

from expmem.database.PineconeClient import PineconeClient
import pandas as pd


def experience_random(datasize: float, chunk_size: int, chunk_overlap: int, ids_file: Optional[str] = None):
    """
    Process documents for experience memory using either specific IDs or random sampling.
    Maintains the exact order of IDs during processing.
    
    Args:
        datasize: Float between 0 and 1 for random sampling
        chunk_size: Size of chunks for text splitting
        chunk_overlap: Overlap between chunks
        ids_file: Optional path to file containing specific IDs
    """
    if datasize > 1 or datasize < 0:
        raise ValueError("Datasize should be between 0 and 1")
    
    pc = PineconeClient(index_name="expmem1", 
                       namespace="expmem1",
                       dimension=1536,
                       metric="cosine")
    
    filename = "humanEval_results_detail2.csv"
    df = pd.read_csv(filename)
    
    # Determine which rows to process while maintaining order
    if ids_file:
        ids = read_ids_from_file(ids_file)
        if ids:
            # Create a new DataFrame with only the specified IDs in the original order
            sample_df = pd.DataFrame()
            for id in ids:
                row = df[df['ID'] == id]
                if not row.empty:
                    sample_df = pd.concat([sample_df, row], ignore_index=True)
            if len(sample_df) == 0:
                print(f"Warning: No matching IDs found in dataset")
                return
        else:
            print(f"Warning: Could not read IDs from {ids_file}, falling back to random sampling")
            sample_df = df.sample(frac=datasize)
    else:
        sample_df = df.sample(frac=datasize)
    
    memory_ids = []
    
    for _, data in sample_df.iterrows():
        document = []
        memory_ids.append(data['ID'])
        
        #save this list to a text file
        with open("memory_ids.txt", "w") as f:
            for id in memory_ids:
                f.write(str(id) + "\n")
        
        # Fetch prompt from MongoDB
        dataset_document = fetch_document(dataset="HumanEval", id=data['ID'])
        prompt = dataset_document.get('prompt')
        
        document.append("Prompt: " + prompt)
        document.append("Code Solution: " + str(data['Code']))
        document.append("Summary Explanation: " + str(data['Summary Explanation']))
        document.append("Detailed Explanation: " + str(data['Detailed Explanation']))
        document.append("Error Analysis: " + str(data['Error Analysis']))
        
        pc.insert_context(context=document, 
                         chunk_size=chunk_size, 
                         chunk_overlap=chunk_overlap)
        
        print(f"Inserted document {data['ID']}")
        
        #print(f"Inserted document {data['ID']}")


# Build Contextual Memory

"""

Class ContextChunk holds the contextual memory attributes
page_content: str - holds the actual string being chunked
prev_context: str - holds the summary of the context that comes before this sentence
next_context: str - holds the summary of the context that comes after this sentence
purpose: str      - holds the purpose of the context 


"""

class ContextChunk(object):
    
    def __init__(self, page_content: str, 
                 prev_context: str, 
                 next_context: str, 
                 purpose: str):
        
        self.page_content = page_content
        self.prev_context = prev_context
        self.next_context = next_context
        self.purpose = purpose



from langchain.text_splitter import TokenTextSplitter
from langchain_core.documents import Document

from expmem.agents.contextual_chunking import *
from expmem.database.mongodb import *
from typing import Optional, List

def contextual_memory(datasize: float = 0.5, ids_file: Optional[str] = None, chunk_size: int = 128):
    """
    Process documents for contextual memory using either specific IDs or random sampling.
    
    Args:
        datasize: Float between 0 and 1 for random sampling (default: 0.5)
        ids_file: Optional path to file containing specific IDs
        chunk_size: Size of chunks for text splitting (default: 128)
    """
    if datasize > 1 or datasize < 0:
        raise ValueError("Datasize should be between 0 and 1")
    
    pc = PineconeClient(index_name=f"contextual{chunk_size}", 
                       namespace=f"contextual{chunk_size}",
                       dimension=1536,
                       metric="cosine")
    
    df = pd.read_csv("humanEval_results_detail2.csv")
    
    # Determine which rows to process
    if ids_file:
        ids = read_ids_from_file(ids_file)
        if ids:
            # Filter dataframe to only include specified IDs
            sample_df = df[df['ID'].isin(ids)]
            if len(sample_df) == 0:
                print(f"Warning: No matching IDs found in dataset")
                return
        else:
            print(f"Warning: Could not read IDs from {ids_file}, falling back to random sampling")
            sample_df = df.sample(frac=datasize)
    else:
        sample_df = df.sample(frac=datasize)
    
    memory_ids = []
    
    for _, data in sample_df.iterrows():
        document = {}
        memory_ids.append(data['ID'])
        
        dataset_document = fetch_document(dataset="HumanEval", id=data['ID'])
        prompt = dataset_document.get('prompt')
        
        # Build document components
        document['solution'] = "Problem :" + prompt + "\n\nSolution: " + data['Code']
        document['summary_exp'] = data['Summary Explanation']
        document['detailed_exp'] = data['Detailed Explanation']
        document['error_analysis'] = data['Error Analysis']
        
        splitter = TokenTextSplitter(encoding_name="cl100k_base", chunk_size=chunk_size, chunk_overlap=0)
        
        # Process Code Solution
        document_ = Document(page_content=str(document['solution']), 
                           metadata={"title": "Code Solution"})
        docs = splitter.split_documents([document_])
        sol_chunks = [
            ContextChunk(
                page_content=doc.page_content,
                prev_context="",
                next_context="",
                purpose="Code Solution"
            ) for doc in docs
        ]
        pc.insert_contextual_memory(context=sol_chunks)
        
        # Process Summary Explanation
        document_ = Document(page_content=str(document['summary_exp']),
                           metadata={"title": "Summary Explanation"})
        docs = splitter.split_documents([document_])
        summary_exp_chunks = [
            ContextChunk(
                page_content=doc.page_content,
                prev_context="",
                next_context="",
                purpose="Summary Explanation"
            ) for doc in docs
        ]
        pc.insert_contextual_memory(context=summary_exp_chunks)
        
        # Process Detailed Explanation
        document_ = Document(page_content=str(document['detailed_exp']), 
                           metadata={"title": "Detailed Explanation"})
        docs_ = splitter.split_documents([document_])
        detailed_exp_chunks = []
        
        for doc in docs_:
            cont = ContextualChunker()
            res = cont(doc.page_content, document)
            chunk = ContextChunk(
                page_content=doc.page_content,
                prev_context=res.prev_context,
                next_context=res.next_context,
                purpose=res.purpose
            )
            detailed_exp_chunks.append(chunk)
        pc.insert_contextual_memory(context=detailed_exp_chunks)
        
        # Process Error Analysis
        document_ = Document(page_content=str(document['error_analysis']), 
                           metadata={"title": "Error Analysis"})
        docs_ = splitter.split_documents([document_])
        error_analysis_chunks = []
        
        for doc in docs_:
            cont = ContextualChunker()
            res = cont(doc.page_content, document)
            chunk = ContextChunk(
                page_content=doc.page_content,
                prev_context=res.prev_context,
                next_context=res.next_context,
                purpose=res.purpose
            )
            error_analysis_chunks.append(chunk)
        pc.insert_contextual_memory(context=error_analysis_chunks)
        
        # Save processed IDs
        with open(f"memory_ids_{chunk_size}2.txt", "w") as f:
            for id in memory_ids:
                f.write(f"{id}\n")
        
        print(f"Processed document {data['ID']}")
        
if __name__ == "__main__":
    
    contextual_memory(datasize=0.5, chunk_size=192, ids_file='/Users/harshavardhank/Desktop/Code/Thesis/Code/expmem/memory_ids.txt')
    # experience_random(datasize=0.5, 
    #                  chunk_size=1024, 
    #                  chunk_overlap=32,
    #                  ids_file='/Users/harshavardhank/Desktop/Code/Thesis/Code/expmem/memory_ids_256.txt')
    # print("Done")