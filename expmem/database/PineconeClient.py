
import os
from dotenv import load_dotenv

load_dotenv()

import time

from pinecone import Pinecone
from pinecone import ServerlessSpec

from typing import Optional, List

from expmem.database.utils import *


class PineconeClient(object):

    def __init__(self, index_name: str, namespace: str, dimension: Optional[int] = None, metric: str = 'cosine'):

        self.index_name = index_name
        self.namespace = namespace
        self.dimension = dimension
        self.metric = metric

        self.client = self._init_pinecone_client(index_name=index_name, 
                                                         dimension=dimension, 
                                                         metric=metric)


    def _init_pinecone_client(self, index_name: str, dimension: Optional[int], metric: str = 'cosine') -> Pinecone:

        pinecone_api_key = os.getenv("PINECONE_API_KEY")

        if pinecone_api_key is not None:
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

        else:
            raise ValueError("Pinecone API key not provided")

        try:
            
            if index_name not in pc.list_indexes().names():
                print(f"Creating Pinecone index {index_name}")

                pc.create_index(

                    name=index_name,
                    dimension=dimension,
                    metric=metric,

                    spec = ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    ),

                    deletion_protection="disabled"
                )
                
                while not pc.describe_index(index_name).status['ready']:
                    time.sleep(1)

            return pc

        except Exception as e:
            raise Exception(f"Error in creating Pinecone index, Exception: {e}")
    
    def _insert_embeddings(self, data: List[str], embeddings: List[List[float]]) -> bool:

        index = self.client.Index(self.index_name)
        
        vectors = []

        ids = [generate_ordered_prefixed_uuid("doc") for _ in range(len(data))]
        
        print("IDs: ", ids)

        for id, d, e in zip(ids, data, embeddings):
            vectors.append({
                "id": id,
                "values": e,
                "metadata": {'text': d.page_content}
            })

        try:
            
            index.upsert(
                vectors=vectors,
                namespace=self.namespace
            )

            print("upserted data")

        except Exception as e:
            print(f"Exception {e} in upserting data")
            return False
        
        
    def _get_ids(self) -> List[int]:
        index = self.client.Index(self.index_name)
        return [id for id in index.list(namespace=self.namespace)]
     
    def insert_context(self, context: List, 
                       chunk_size: Optional[int] = None, 
                       chunk_overlap: Optional[int] = None) -> None:

        if isinstance(context, str):
            context = [context]

        if chunk_size is not None:
            context = recursive_chunking(context, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            text = [d.page_content for d in context]
            embeddings = create_embeddings(text)
            
        else:
            embeddings = create_embeddings(context)

        self._insert_embeddings(context, embeddings)
        
    
    def insert_contextual_memory(self, context: List):
        
        """ 
        
        Context is a List of the Context object
        Context object : page_content, prev_context, next_context, purpose attributes
        We embed the page_content and store it in Pinecone, the rest attributes will be metadata
        
        """
        
        #Prepare data
        text = [d.page_content for d in context]
        metadata = [{'prev_context': d.prev_context, 
                     'next_context': d.next_context, 
                     'purpose': d.purpose,
                     'text': d.page_content } for d in context]
        
        # metadata = [{
        #             'text': f"chunk: {d.page_content}, " \
        #                     f"purpose: {d.purpose}, " \
        #                     f"prev_context: {d.prev_context}, " \
        #                     f"next_context: {d.next_context}"
        #                     } for d in context]

        
        embeddings = create_embeddings(text)
        
        ids = [generate_ordered_prefixed_uuid("contextual_memory") for _ in range(len(context))]
        
        index = self.client.Index(self.index_name)
        
        vectors = []
    
        
        for id, embed, meta in zip(ids, embeddings, metadata):
            vectors.append({
                "id": id,
                "values": embed,
                "metadata": meta
            })

        try:
            
            index.upsert(
                vectors=vectors,
                namespace=self.namespace
            )

            print("upserted data")

        except Exception as e:
            print(f"Exception {e} in upserting data")
            return False
        

        
        