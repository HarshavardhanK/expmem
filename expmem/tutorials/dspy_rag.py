import os

from dotenv import load_dotenv
load_dotenv()

import requests
import ujson
import torch
import functools
import dspy

from litellm import embedding as Embed

"""
RAG (Retrieval-Augmented Generation) Tutorial

This script demonstrates a basic implementation of a RAG system using DSPy.
It includes data loading, retrieval setup, RAG module definition, and optimization.

The script is divided into several sections, each with single-responsibility functions:
1. Data Download
2. Model Setup
3. Data Loading
4. Evaluation Setup
5. Retriever Setup
6. RAG Module Definition
7. Optimization
8. Main Execution

Make sure to install the required dependencies:
pip install dspy torch litellm requests ujson
"""

# ------------------------
# 1. Data Download
# ------------------------

def download_file(url):
    """
    Downloads a single file from the given URL.
    
    Args:
        url (str): The URL of the file to download.
    """
    filename = os.path.basename(url)
    remote_size = int(requests.head(url, allow_redirects=True).headers.get('Content-Length', 0))
    local_size = os.path.getsize(filename) if os.path.exists(filename) else 0

    if local_size != remote_size:
        print(f"Downloading '{filename}'...")
        with requests.get(url, stream=True) as r, open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def download_all_data():
    """
    Downloads all necessary data files for the RAG system.
    """
    urls = [
        'https://huggingface.co/dspy/cache/resolve/main/ragqa_arena_tech_500.json',
        'https://huggingface.co/datasets/colbertv2/lotte_passages/resolve/main/technology/test_collection.jsonl',
        'https://huggingface.co/dspy/cache/resolve/main/index.pt'
    ]

    for url in urls:
        download_file(url)

# ------------------------
# 2. Model Setup
# ------------------------

def setup_model(model: str):

    model = dspy.OpenAI(model=model, 
                    max_tokens=500, 
                    api_key=os.getenv("OPENAI_API_KEY"))

    return model

# ------------------------
# 3. Data Loading
# ------------------------

def load_data():
    """
    Loads the dataset and splits it into train/val/dev/test sets.
    
    Returns:
        tuple: Contains the following elements:
            - trainset (list): Training dataset.
            - valset (list): Validation dataset.
            - devset (list): Development dataset.
            - testset (list): Test dataset.
    """
    with open('ragqa_arena_tech_500.json') as f:
        data = [dspy.Example(**d).with_inputs('question') for d in ujson.load(f)]
        return data[:50], data[50:150], data[150:300], data[300:500]

# ------------------------
# 4. Evaluation Setup
# ------------------------

def setup_evaluation(devset):
    """
    Configures the evaluation metric and function.
    
    Args:
        devset (list): Development dataset.
    
    Returns:
        dspy.Evaluate: Configured evaluation function.
    """
    metric = SemanticF1()
    return dspy.Evaluate(devset=devset, metric=metric, num_threads=24, display_progress=True, display_table=3)

# ------------------------
# 5. Retriever Setup
# ------------------------

def load_corpus():
    """
    Loads the corpus from the JSONL file.
    
    Returns:
        list: List of documents in the corpus.
    """
    with open("test_collection.jsonl") as f:
        return [ujson.loads(line) for line in f]

def load_index():
    """
    Loads the pre-computed index.
    
    Returns:
        torch.Tensor: The loaded index.
    """
    return torch.load('index.pt', weights_only=True)

def create_search_function(corpus, index):
    """
    Creates the search function using the corpus and index.
    
    Args:
        corpus (list): List of documents in the corpus.
        index (torch.Tensor): Pre-computed index.
    
    Returns:
        function: The search function.
    """
    max_characters = 4000  # >98th percentile of document lengths

    @functools.lru_cache(maxsize=None)
    def search(query, k=5):
        query_embedding = torch.tensor(Embed(input=query, model="text-embedding-3-small").data[0]['embedding'])
        topk_scores, topk_indices = torch.matmul(index, query_embedding).topk(k)
        topK = [dict(score=score.item(), **corpus[idx]) for idx, score in zip(topk_indices, topk_scores)]
        return [doc['text'][:max_characters] for doc in topK]

    return search

def setup_retriever():
    """
    Sets up the retrieval function using pre-computed embeddings.
    
    Returns:
        function: The search function.
    """
    corpus = load_corpus()
    index = load_index()
    return create_search_function(corpus, index)

# ------------------------
# 6. RAG Module Definition
# ------------------------

class RAG(dspy.Module):
    """
    Retrieval-Augmented Generation (RAG) module.
    
    This module combines retrieval and generation to answer questions based on retrieved context.
    """
    def __init__(self, search_func, num_docs=5):
        self.search = search_func
        self.num_docs = num_docs
        self.respond = dspy.ChainOfThought('context, question -> response')

    def forward(self, question):
        """
        Performs the RAG process: retrieves relevant documents and generates a response.
        
        Args:
            question (str): The input question to be answered.
        
        Returns:
            dspy.Prediction: Contains the generated response and reasoning.
        """
        context = self.search(question, k=self.num_docs)
        print(type(context))
        return self.respond(context=context, question=question)

# ------------------------
# 7. Optimization
# ------------------------

def optimize_rag(rag, trainset, valset, metric):
    """
    Optimizes the RAG module using DSPy's MIPRO optimizer.
    
    Args:
        rag (RAG): The RAG module to optimize.
        trainset (list): Training dataset.
        valset (list): Validation dataset.
        metric (dspy.Evaluate): Evaluation metric.
    
    Returns:
        RAG: Optimized RAG module.
    """
    tp = dspy.MIPROv2(metric=metric, auto="medium", num_threads=24)
    return tp.compile(rag, trainset=trainset, valset=valset,
                      max_bootstrapped_demos=2, max_labeled_demos=2,
                      requires_permission_to_run=False)

# ------------------------
# 8. Main Execution
# ------------------------

def main():
    # Download necessary data
    download_all_data()

    # Set OpenAI API key
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

    # Setup model
    lm = setup_model(model='gpt-4o-mini-2024-07-18')
    dspy.settings.configure(lm=lm)

    # Load data
    trainset, valset, devset, testset = load_data()

    # Setup evaluation
    #evaluate = setup_evaluation(devset)

    # Setup retriever
    search = setup_retriever()

    # Create and evaluate baseline RAG
    rag = RAG(search)
    res = rag(question="what are high memory and low memory on linux?")
    print(type(res))
    # print("Evaluating baseline RAG:")
    # evaluate(rag)

    # # Optimize RAG
    # optimized_rag = optimize_rag(rag, trainset, valset, evaluate.metric)
    
    # # Evaluate optimized RAG
    # print("\nEvaluating optimized RAG:")
    # evaluate(optimized_rag)

    # # Example usage
    # question = "What are high memory and low memory on Linux?"
    # print(f"\nExample question: {question}")
    # print("Baseline RAG answer:")
    # print(rag(question=question).response)
    # print("\nOptimized RAG answer:")
    # print(optimized_rag(question=question).response)

    # # Save optimized RAG
    # optimized_rag.save("optimized_rag.json")
    # print("\nOptimized RAG saved to 'optimized_rag.json'")

if __name__ == "__main__":
    main()

"""
This tutorial demonstrates a basic RAG system implementation using DSPy.
Key components include:
1. Data download and loading
2. Model setup
3. Retriever implementation using pre-computed embeddings
4. RAG module definition combining retrieval and generation
5. Optimization using DSPy's MIPRO optimizer
6. Evaluation and comparison of baseline and optimized RAG models

To use this script:
1. Ensure all required libraries are installed
2. Run the script to see the full RAG pipeline in action
3. Modify the `main()` function to experiment with different questions or configurations

Note: This script assumes access to the necessary data files and may require
adjustments based on your specific environment and data availability.
"""