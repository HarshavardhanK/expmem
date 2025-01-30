from llm_sandbox import SandboxSession
import pandas as pd
import signal
from typing import Dict
import os
import json
from threading import Thread
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

def setup_mongodb(database: str, collection: str) -> tuple:
    mongodb_uri = os.getenv("MONGODB_URI")
    client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
    
    db = client[database]
    coll = db[collection]
    
    return db, coll

def timeout_handler(_, __):
    raise TimeoutError()

def to_jsonl(dict_data, file_path):
    with open(file_path, 'a') as file:
        json_line = json.dumps(dict_data)
        file.write(json_line + os.linesep)

class PropagatingThread(Thread):
    def run(self):
        self.exc = None
        try:
            if hasattr(self, '_Thread__target'):
                self.ret = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
            else:
                self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e

    def join(self, timeout=None):
        super(PropagatingThread, self).join(timeout)
        if self.exc:
            raise self.exc
        return self.ret

def function_with_timeout(func, args, timeout):
    result_container = []
    
    def wrapper():
        result_container.append(func(*args))
    
    thread = PropagatingThread(target=wrapper)
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        raise TimeoutError()
    else:
        return result_container[0]

def evaluate_code(code: str, timeout: int = 5):
    try:
        print('<ExecutingCode>')
        print(code)
        print('</ExecutingCode>')
        
        function_with_timeout(
            exec,
            (code, globals()),
            timeout
        )
        return "passed"
    except Exception as e:
        return f"failed: {e}"

def get_processed_ids(output_path):
    """Read the existing JSONL file and return a set of already processed IDs"""
    processed_ids = set()
    if os.path.exists(output_path):
        with open(output_path, 'r') as file:
            for line in file:
                try:
                    data = json.loads(line.strip())
                    if 'ID' in data:
                        processed_ids.add(data['ID'])
                except:
                    continue
    return processed_ids

def construct_full_code(source_code: str, problem_id: str, context_collection) -> str:
    """Construct full code by combining source code with test and entry point from MongoDB"""
    # Get context from MongoDB
    context = context_collection.find_one({'ID': problem_id})
    
    if not context:
        return "Context not found in MongoDB"
    
    # Construct code following the specified format
    typing_import = "from typing import *\n" if "from typing import *" not in source_code else ""
    
    full_code = (
        typing_import +
        source_code + "\n" +
        context['test'] + "\n" +
        f"check({context['entry_point'].strip('\"')})"  # Remove quotes from entry_point
    )
    
    return full_code

def process_csv(csv_path: str, output_path: str = "results.jsonl"):
    """Process CSV file and evaluate code blocks"""
    # Setup MongoDB connection
    _, context_collection = setup_mongodb("HumanEval", "context")
    
    # Get already processed IDs
    processed_ids = get_processed_ids(output_path)
    print(f"Found {len(processed_ids)} already processed samples")
    
    # Initialize counters
    passed_count = 0
    failed_count = 0
    skipped_count = 0
    
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Remove duplicates based on ID
    df = df.drop_duplicates(subset=['ID'])
    total_unique_samples = len(df)
    
    print(f"\nStarting evaluation of remaining samples from {total_unique_samples} unique samples...\n")
    
    # Initialize sandbox session
    session = SandboxSession(lang="python", keep_template=True)
    session.open()
    
    # Process each row
    for index, row in df.iterrows():
        try:
            # Skip if already processed
            if row['ID'] in processed_ids:
                skipped_count += 1
                print(f"Skipping {row['ID']}: already processed")
                continue
            
            # Check if Full_Code exists, if not construct it
            if 'Full_Code' not in row or pd.isna(row['Full_Code']):
                if 'Code' in row and not pd.isna(row['Code']):
                    code = construct_full_code(row['Code'], row['ID'], context_collection)
                    print(f"Constructed full code for {row['ID']}")
                else:
                    raise ValueError("Neither Full_Code nor Code found in row")
            else:
                code = row['Full_Code']
            
            # Evaluate code using sandbox
            res = session.run(code)
            result = "passed" if 'Error' not in res.text else f"failed: {res.text}"
            
            # Update counters
            if result == "passed":
                passed_count += 1
            else:
                failed_count += 1
            
            # Create result dictionary with context
            result_dict = {
                'ID': row['ID'],
                'result': result,
                'original_code': code,
                'context': row.get('Context', '')
            }
            
            # Save to JSONL
            to_jsonl(result_dict, output_path)
            
            print(f"Processed {row['ID']}: {result}")
            
        except Exception as e:
            failed_count += 1
            print(f"Error processing row {index}: {e}")
            to_jsonl({
                'ID': row['ID'] if 'ID' in row else f"row_{index}",
                'result': f"failed: {e}",
                'original_code': code if 'code' in locals() else None,
                'context': row.get('Context', '')
            }, output_path)
    
    # Close sandbox session
    session.close()
    
    # Print final summary
    print("\n" + "="*50)
    print("EVALUATION SUMMARY")
    print("="*50)
    print(f"Total unique samples: {total_unique_samples}")
    print(f"Already processed (skipped): {skipped_count}")
    print(f"Newly processed: {passed_count + failed_count}")
    if passed_count + failed_count > 0:
        print(f"  Passed: {passed_count} ({(passed_count/(passed_count + failed_count)*100):.2f}%)")
        print(f"  Failed: {failed_count} ({(failed_count/(passed_count + failed_count)*100):.2f}%)")
    print("="*50)
    
    return {
        'total_unique': total_unique_samples,
        'skipped': skipped_count,
        'passed': passed_count,
        'failed': failed_count
    }

if __name__ == '__main__':
    process_csv('/Users/harshavardhank/Desktop/Code/Thesis/Code/expmem/humanEval_memory_naive4.csv', 'results_mem_2.jsonl')