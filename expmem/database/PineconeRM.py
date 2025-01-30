
''' 
This class defines a Pinecone Retriever Model compatible with DSPy.

'''

import time

import os
from dotenv import load_dotenv
load_dotenv()

from pinecone import Pinecone
from pinecone import ServerlessSpec

from openai import OpenAI

from typing import List, Optional, Union

import backoff

from dspy import Retrieve, Prediction
from dsp.utils.settings import settings
from dsp.utils import dotdict

class PineconeRetriever(Retrieve):

    def __init__(
            self,
            pinecone_api: str,
            pinecone_index_name: str,
            pinecone_namespace: str,
            openai_embed_model: str,
            openai_api_key: str,
            dimension: int = 1536,
            metric: str = "cosine",
            top_k: int = 3
    ):
        
        super().__init__(k = top_k)
        self._top_k = top_k

        if openai_embed_model is not None:
            self._openai_embed_model = openai_embed_model

            if openai_api_key is not None:
                self._openai_api_key = openai_api_key
                os.environ["OPENAI_API_KEY"] = openai_api_key
                
            else:
                raise ValueError("OpenAI API key not provided")
            
        else:
            raise ValueError("OpenAI model not provided")
        
        if pinecone_api is not None:
            self._namespace = pinecone_namespace
            self._pinecone_api_key = pinecone_api
            self._pc = Pinecone(api_key=self._pinecone_api_key)

            try:

                if pinecone_index_name is None:
                    raise ValueError("Pinecone index name not provided")
                
                elif dimension is None:
                    raise ValueError("Dimension not provided")
                
                elif metric is None:
                    raise ValueError("Metric not provided")
                
                self._pinecone_index_name = pinecone_index_name
        
                if self._pinecone_index_name not in self._pc.list_indexes().names():
                    print(f"Creating Pinecone index {self._pinecone_index_name}")

                    self._pc.create_index(

                        name=self._pinecone_index_name,
                        dimension=dimension,
                        metric=metric,

                        spec = ServerlessSpec(
                            cloud="aws",
                            region="us-east-1"
                        ),

                        deletion_protection="disabled"
                    )
                    
                    while not self._pc.describe_index(self._pinecone_index_name).status['ready']:
                        time.sleep(1)

            except Exception as e:
                raise Exception(f"Error in creating Pinecone index, Exception: {e}")
            

    def set_chunk_size(self, chunk_size: int = 512, chunk_overlap: int = 16) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def _recursive_chunking(self, text: List[str]) -> List[str]:

        # LangChain Chunking

        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter

        except ImportError as imp:
            raise ModuleNotFoundError(f"Error in importing RecursiveCharacterTextSplitter from langchain.text_splitter, Exception: {imp}")

        try:

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size = self._chunk_size,
                chunk_overlap = self._chunk_overlap
            )

            docs = text_splitter.create_documents(text)

            return docs
        
        except Exception as e:
            raise Exception(f"Error in chunking text, Exception: {e}")


    def _get_embeddings(self, queries: List[str], chunking: bool = False) -> List[List[float]]:

        try:

            client = OpenAI(api_key=self._openai_api_key)

            if chunking:
                print("Chunking text")
                docs = self._recursive_chunking(queries)
                queries = [d.page_content for d in docs]

            embedding = client.embeddings.create(
                input=queries,
                model=self._openai_embed_model
            )

            return [rec.embedding for rec in embedding.data]
        
        except Exception as e:
            raise Exception(f"Error in getting embeddings, Exception: {e}")

    def forward(self, query: Union[str, List[str]], k: Optional[int] = None) -> Prediction:

        if k is None:
            k = self._top_k

        queries = [query] if isinstance(query, str) else query
        queries = [q for q in queries if q] #Filter out empty strings

        embeddings = self._get_embeddings(queries)


        if len(queries) == 1:

            results_dict = self._pc.Index(self._pinecone_index_name).query(vector=embeddings, 
                                                                           namespace=self._namespace, 
                                                                           top_k=k, 
                                                                           include_metadata=True)
            
            sorted_results = sorted(results_dict['matches'], key=lambda x: x.get('score', 0.0), reverse=True)
            #print(results_dict)
            passages = [result['metadata']['text'] for result in sorted_results]

            passages = [dotdict({"long_text": passage}) for passage in passages]
            
            return passages
        
        else:

            passages_scores = {}

            for embedding in embeddings:
                results_dict = self._pc.Index(self._pinecone_index_name).query(vector=embedding, 
                                                                               namespace=self._namespace,
                                                                               top_k=k * 3, 
                                                                               include_metadata=True)

                for result in results_dict['matches']:
                    passages_scores[result["metadata"]['text']] = passages_scores.get(result['metadata']['text'], 0.0) + result["score"]

            sorted_passages = sorted(passages_scores.items(), key=lambda x: x[1], reverse=True)[: self._top_k]

            return Prediction(passages=[dotdict({"long_text": passage}) for passage, _ in sorted_passages])
