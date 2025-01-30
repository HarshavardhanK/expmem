
import time

import os
from dotenv import load_dotenv
load_dotenv()

from pinecone import Pinecone
from pinecone import ServerlessSpec

from openai import OpenAI

def create_embeddings(text: list, MODEL: str) -> list:

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        embeddings = client.embeddings.create(model=MODEL, input=text)
        return embeddings
    
    except Exception as e:
        print(e)
        return None

# LangChain Chunking
from langchain.text_splitter import RecursiveCharacterTextSplitter

def get_pinecone_client(index_name: str, dimension: int, metric: str) -> Pinecone:

    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

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
    


from typing import Tuple

def chunking_recursive(text: list) -> list:

    # Check for which metric to use appropriately
    # Dotproduct or Cosine similarrity
    # Hybrid search requires dot product similarity
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 128,
        chunk_overlap = 8
    )

    docs = text_splitter.create_documents(text)

    return docs

def generate_pinecone_embeddings(data: list) -> list:

    pc = get_pinecone_client()

    try :

        embeddings = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[d.page_content for d in data],
            parameters={"input_type": "passage", "truncate": "END"}
        )

        return embeddings

    except Exception as e:
        print(e)
        return None

def insert_embeddings(data: list, embeddings: list) -> bool:

    pc = get_pinecone_client(index_name="example", 
                             dimension=len(embeddings[0]), 
                             metric="cosine")

    index = pc.Index("example")
    vectors = []

    ids = [str(n) for n in range(len(data))]

    for id, d, e in zip(ids, data, embeddings):
        vectors.append({
            "id": id,
            "values": e,
            "metadata": {'text': d.page_content}
        })

    try:
        
        index.upsert(
            vectors=vectors,
            namespace="demo"
        )

        print("upserted data")

    except Exception as e:
        print(f"Exception {e} in upserting data")
        return False


def query_pinecone(text: str, index_name: str, embed_model: str):


    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    xq = client.embeddings.create(input=text, model=embed_model).data[0].embedding
    print('Xq:', xq)

    pc = get_pinecone_client(index_name=index_name, 
                             dimension=len(xq), 
                             metric="cosine")
    
    index = pc.Index(index_name)

    print([xq])

    res = index.query(namespace="demo", 
                      vector=[xq], 
                      top_k=5, 
                      include_metadata=True)

    print(res)

    for match in res['matches']:
        print(f"{match['score']:.2f}: {match['metadata']['text']}")


if __name__ == '__main__':

    text = ["this is harsha he stays in riverside, ca and he is from udupi india",
            "harsha likes going to the beach and he loves to play cricket",
            "harsha is a software engineer and he works at google",
            "harsha likes trekking"]

    docs = chunking_recursive(text=text)

    text_data = [d.page_content for d in docs]

    print("text_data:", text_data)

    MODEL = "text-embedding-3-small"

    openai_embeddings = create_embeddings(text_data, MODEL)
    #print(openai_embeddings)
    embeds = [rec.embedding for rec in openai_embeddings.data]

    embed_len = len(embeds[0])

    pc = get_pinecone_client(index_name="example", 
                             dimension=embed_len, 
                             metric="cosine")

    insert = insert_embeddings(docs, embeds)

    query_text = "where does harsha stay"

    query_pinecone(text=query_text, 
          index_name="example", 
          embed_model=MODEL)
    