import json
from typing import Dict, Tuple
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os

from dotenv import load_dotenv
load_dotenv()

def setup_mongodb(database: str, collection: str) -> tuple:
    mongodb_uri = os.getenv("MONGODB_URI")
    client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
    
    db = client[database]
    coll = db[collection]
    
    return db, coll

def save_to_jsonl(data: Dict, filepath: str):
    """Save comparison data to JSONL file"""
    with open(filepath, 'a') as f:
        json_line = json.dumps(data)
        f.write(json_line + '\n')

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

def load_expmem_results(jsonl_path: str, context_collection) -> Dict[str, Dict]:
    """Load results from Expmem JSONL file."""
    results = {}
    with open(jsonl_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            
            # Check if Full_Code exists, if not construct it
            if 'original_code' not in data and 'Code' in data:
                full_code = construct_full_code(data['Code'], data['ID'], context_collection)
            else:
                full_code = data.get('original_code', 'Not found')
            
            results[data['ID']] = {
                'passed': data['result'] == 'passed',
                'full_code': full_code,
                'context': data.get('context', '')
            }
    return results

def load_mapcoder_results(jsonl_path: str, context_collection) -> Dict[str, Dict]:
    """Load results from MapCoder JSONL file and construct full code using MongoDB context."""
    results = {}
    with open(jsonl_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            task_id = data['task_id']
            
            # Get the source code
            source_code = data['source_codes'][0] if data['source_codes'] else ""
            
            # Construct full code using MongoDB context
            full_code = construct_full_code(source_code, task_id, context_collection)
            
            results[task_id] = {
                'passed': data['is_solved'],
                'full_code': full_code
            }
    return results

def compare_results(expmem_path: str, mapcoder_path: str, context_collection, output_path: str):
    """Compare results from both JSONL files and save divergent cases to JSONL."""
    # Load results
    expmem_results = load_expmem_results(expmem_path, context_collection)  # Pass context_collection
    mapcoder_results = load_mapcoder_results(mapcoder_path, context_collection)
    #expmem_results2 = load_expmem_results(expmem_path2, context_collection)
    
    # Track statistics
    total_problems = 0
    matching_results = 0
    divergent_results = 0
    
    # Create new output file (overwrite if exists)
    if os.path.exists(output_path):
        os.remove(output_path)
    
    # Get all unique IDs
    all_ids = set(expmem_results.keys()) | set(mapcoder_results.keys())
    
    print(f"\nAnalyzing {len(all_ids)} problems...")
    
    # Sort IDs for consistent output
    for problem_id in sorted(all_ids):
        total_problems += 1
        
        expmem_data = expmem_results.get(problem_id, {'passed': False, 'full_code': 'Not found', 'context': ''})
        mapcoder_data = mapcoder_results.get(problem_id, {'passed': False, 'full_code': 'Not found'})
        
        # Check if results match
        results_match = expmem_data['passed'] == mapcoder_data['passed']
        
        if results_match:
            matching_results += 1
            continue  # Skip saving matching results
            
        # If we get here, results are divergent
        divergent_results += 1
        
        # Create comparison result for divergent case
        comparison = {
            'ID': problem_id,
            'expmem_passed': expmem_data['passed'],
            'mapcoder_passed': mapcoder_data['passed'],
            'expmem_fullcode': expmem_data['full_code'],
            'mapcoder_fullcode': mapcoder_data['full_code'],
            'context': expmem_data['context']
        }
        
        # Save divergent case to JSONL
        save_to_jsonl(comparison, output_path)
        
        # Print divergent case to console
        print(f"\nDivergent Case - ID: {problem_id}")
        print(f"expmem_passed: {expmem_data['passed']}")
        print(f"MapCoder_passed: {mapcoder_data['passed']}")
        print("expmem_fullcode: ")
        print("```python")
        print(expmem_data['full_code'])
        print("```")
        print("mapcoder_fullcode: ")
        print("```python")
        print(mapcoder_data['full_code'])
        print("```")
        print("Context:")
        print(expmem_data['context'])
        print("-" * 80)
    
    # Print summary statistics
    print("\nSUMMARY")
    print("=" * 50)
    print(f"Total problems analyzed: {total_problems}")
    print(f"Matching results: {matching_results}")
    print(f"Divergent results: {divergent_results}")
    print(f"Agreement rate: {(matching_results/total_problems)*100:.2f}%")
    print(f"\nDivergent cases saved to: {output_path}")

def main():
    # Add paths to your JSONL files
    expmem_path = "results_mem_2.jsonl"
    #expmem_path2 = "results_mem_128.jsonl"
    mapcoder_path = "/Users/harshavardhank/Desktop/Code/Thesis/Code/MapCoder/outputs/GPT4oMini-MapCoder-HumanEval-Python3-0-1.jsonl"
    output_path = "mapcoder_naive_mem_2_comparison.jsonl"
    
    try:
        # Setup MongoDB connection
        _, context_collection = setup_mongodb("HumanEval", "context")
        
        # Compare results and save divergent cases to JSONL
        compare_results(expmem_path, mapcoder_path, context_collection, output_path)
        
    except Exception as e:
        print(f"Error during comparison: {str(e)}")
        raise e

if __name__ == "__main__":
    main()