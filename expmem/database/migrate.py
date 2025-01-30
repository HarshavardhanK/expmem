import pandas as pd
import re
from typing import Dict, Any
from pymongo import MongoClient
from io import StringIO

from expmem.database.mongodb import setup_mongodb, append_result

def process_dataframe_row(row: pd.Series) -> Dict[str, Any]:

    data = row.where(pd.notna(row), None).to_dict()
    data = {str(k): v for k, v in data.items()}
    
    return data

def save_to_mongodb(filepath: str, experiment_id: str):

    _, collection = setup_mongodb(
        database="HumanEval",
        collection="response"
    )
    
    df = pd.read_csv(filepath, delimiter=',', quotechar='"', escapechar='\\', engine='python')
    
    # Process each row
    for _, row in df.iterrows():
        
        data = process_dataframe_row(row)
            
        exec_res = {
            'prediction': data.get('Error Analysis', ''),
            'result': data.get('Result', ''),
            'full_code': data.get('Full_Code', '')
        }
        
        _ = append_result(
            data=data,
            ID='ID',
            code=data.get('Code', None),
            exec_res=exec_res,
            summary=data.get('Summary Explanation', None),
            detailed=data.get('Detailed Explanation', None),
            collection=collection,
            experiment_id=experiment_id,
            context=data.get('Context', None)
        )



# Migrate the dataset context to MongoDB
from expmem.datasets.DatasetFactory import DatasetFactory

def migrate_dataset(dataset_name: str):
    
    if dataset_name not in ['HumanEval', 'MBPP']:
        raise ValueError("Dataset not found")
    
    data = DatasetFactory(dataset_name)
    dataset_ = data.get_dataset()
    documents = []
    
    for sample in dataset_:
        #prepare insert document
        doc = {
            'ID': sample[dataset_._id],
            'prompt': sample.prompt,
            'test': sample.test,
            'sample_io': sample.sample_io,
            'entry_point': sample.entry_point,
            'canonical_solution': sample.canonical_solution,
        }
        
        documents.append(doc)
        
    #Insert to MongoDB
    _, collection = setup_mongodb(
        database=dataset_name,
        collection="context"
    )
    
    collection.insert_many(documents)

if __name__ == "__main__":

    # save_to_mongodb(filepath='/Users/harshavardhank/Desktop/Code/Thesis/Code/expmem/humanEval_simple3.csv', 
    #                 experiment_id='humanEval_simple3')
    
    migrate_dataset('MBPP')