import os
from dotenv import load_dotenv

load_dotenv()

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from typing import Dict, Any

def setup_mongodb(database: str, collection: str) -> tuple:
    
    mongodb_uri = os.getenv("MONGODB_URI")
    client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
    
    db = client[database]
    coll = db[collection]
    
    return db, coll


#MongoDB function to fetch document through dataset index
def fetch_document(dataset: str, id: str):
    
    _, coll = setup_mongodb(
        database=dataset,
        collection='context'
    )
    
    document = coll.find_one({'ID': id})
    
    return document

def append_result(data: Dict[str, Any], 
                 ID: str, 
                 code: str, 
                 exec_res: Dict[str, Any], 
                 summary: str, 
                 detailed: str,
                 collection: str,
                 experiment_id: str,
                 context: str = None) -> Dict[str, Any]:

    result_doc = {
        'Experiment_ID': experiment_id,
        'ID': data[ID],
        'Context': context,
        'Error_Analysis': exec_res['prediction'],
        'Summary_Explanation': summary,
        'Detailed_Explanation': detailed,
        'Result': exec_res['result'],
        'Code': code,
    }
    
    
    collection.update_one(
        {'ID': data[ID], 'Experiment_ID': experiment_id},
        {'$set': result_doc},
        upsert=True
    )
    
    return result_doc

# TODO: Create function to store experiment ID. 

"""

An Experiment will have:
 - experiment_id
 - model_name
 - hyperparameters: {temperature, top_p, max_tokens, stop_sequence}
 - pinecone params: {index_name, namespace, dimension, metric, top_k}
 - date
 - dataset
 - notes
 - evaluation: {pass@1, other evaluation metrics}
 - completed: True/False { this will indicate if the whole dataset was processed or not }


"""

#TODO: Create function to store the dataset