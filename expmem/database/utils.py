from typing import List, Optional, Union

import time


import os
from dotenv import load_dotenv
load_dotenv()

from pinecone import Pinecone
from pinecone import ServerlessSpec

from openai import OpenAI

import uuid
import time

def generate_ordered_prefixed_uuid(prefix):
    
    timestamp = int(time.time() * 1000)
    unique_id = uuid.uuid4().hex
    ordered_prefixed_uuid = f"{prefix}_{timestamp}_{unique_id}"
    
    return ordered_prefixed_uuid


def recursive_chunking(text: List[str], 
                       chunk_size: Optional[int] = 512, 
                       chunk_overlap: Optional[int] = 16) -> List[str]:
        
        if isinstance(text, str):
             text = [text]

        # LangChain Chunking

        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter

        except ImportError as imp:
            raise ModuleNotFoundError(f"Error in importing RecursiveCharacterTextSplitter from langchain.text_splitter, Exception: {imp}")

        try:

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size = chunk_size,
                chunk_overlap = chunk_overlap
            )

            #print("Text is: ", text)
            docs = text_splitter.create_documents(text)

            return docs
        
        except Exception as e:
            raise Exception(f"Error in chunking text, Exception: {e}")


def create_embeddings(context: List[str], model: str =  "text-embedding-3-small") -> list:

    if isinstance(context, list) == False:
         raise ValueError("Context should be a list of strings")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    #print('Context is: ', context)

    try:

        embedding = client.embeddings.create(
                input=context,
                model=model,
        )

        return [rec.embedding for rec in embedding.data]
    
    except Exception as e:
        print(e)
        return None  

