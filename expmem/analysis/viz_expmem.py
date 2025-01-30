# import streamlit as st
# import json
# from typing import Dict
# from pymongo import MongoClient
# from pymongo.server_api import ServerApi
# import os

# from dotenv import load_dotenv
# load_dotenv()

# def setup_mongodb(database: str, collection: str) -> tuple:
#     mongodb_uri = os.getenv("MONGODB_URI")
#     client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
    
#     db = client[database]
#     coll = db[collection]
    
#     return db, coll

# def construct_full_code(source_code: str, problem_id: str, context_collection) -> str:
#     """Construct full code by combining source code with test and entry point from MongoDB"""
#     # Get context from MongoDB
#     context = context_collection.find_one({'ID': problem_id})
    
#     if not context:
#         return "Context not found in MongoDB"
    
#     # Construct code following the specified format
#     typing_import = "from typing import *\n" if "from typing import *" not in source_code else ""
    
#     full_code = (
#         typing_import +
#         source_code + "\n" +
#         context['test'] + "\n" +
#         f"check({context['entry_point'].strip('\"')})"
#     )
    
#     return full_code

# def load_comparison_results(jsonl_path1: str, jsonl_path2: str) -> tuple[Dict, Dict]:
#     """Load comparison results from two JSONL files."""
#     results1, results2 = {}, {}
    
#     with open(jsonl_path1, 'r') as f:
#         for line in f:
#             data = json.loads(line)
#             results1[data['ID']] = data
            
#     with open(jsonl_path2, 'r') as f:
#         for line in f:
#             data = json.loads(line)
#             results2[data['ID']] = data
            
#     return results1, results2

# def display_code_block(title: str, code: str, is_success: bool, context: str = None):
#     """Display code with improved formatting and syntax highlighting."""
#     with st.container():
#         # Header with status
#         col1, col2 = st.columns([3, 1])
#         with col1:
#             st.markdown(f"#### {title}")
#         with col2:
#             if is_success:
#                 st.markdown('✅ Success')
#             else:
#                 st.markdown('❌ Failed')
        
#         # Display full code without any processing
#         st.code(code.strip(), language='python')
        
#         # Display context section
#         st.markdown("#### Context")
#         if context:
#             st.markdown(context)
#         else:
#             st.markdown("*No Context used*")

# def main():
#     st.set_page_config(
#         layout="wide",
#         page_title="ExpMem Comparison Analysis",
#         initial_sidebar_state="expanded"
#     )
    
#     # File paths and names
#     file1_path = "/Users/harshavardhank/Desktop/Code/Thesis/Code/expmem/results_detail.jsonl"  # Update this path
#     file2_path = "/Users/harshavardhank/Desktop/Code/Thesis/Code/expmem/results_mem_2.jsonl"  # Update this path
#     file1_name = "No Memory"  # Update this name
#     file2_name = "Memory 1 (1024 Char chunking)"  # Update this name
    
#     # Setup MongoDB connection
#     db, context_collection = setup_mongodb("HumanEval", "context")  # Update with your DB and collection names
    
#     st.title(f"{file1_name} vs {file2_name} Comparison")
    
#     # Load comparison results
#     try:
#         results1, results2 = load_comparison_results(file1_path, file2_path)
        
#         # Get common problem IDs and sort them
#         common_ids = sorted(set(results1.keys()) & set(results2.keys()))
        
#         # Display metrics
#         st.sidebar.header("Analysis Metrics")
#         total_common = len(common_ids)
#         st.sidebar.metric("Common Cases", total_common)
        
#         # Problem selection
#         st.sidebar.header("Problem Selection")
#         problem_list = [(id, f"{id} ({file1_name}: {'✓' if results1[id].get('result') == 'passed' else '✗'}, " +
#                         f"{file2_name}: {'✓' if results2[id].get('result') == 'passed' else '✗'})")
#                        for id in common_ids]
        
#         selected_problem = st.sidebar.selectbox(
#             "Select Problem ID",
#             [id for id, _ in problem_list],
#             format_func=lambda x: next(label for id, label in problem_list if id == x)
#         )
        
#         if selected_problem:
#             results1_problem = results1[selected_problem]
#             results2_problem = results2[selected_problem]
            
#             # Construct full code for both versions
#             code1 = construct_full_code(
#                 results1_problem['original_code'],
#                 selected_problem,
#                 context_collection
#             )
            
#             code2 = construct_full_code(
#                 results2_problem['original_code'],
#                 selected_problem,
#                 context_collection
#             )
            
#             # Create columns for side-by-side comparison
#             st.markdown(f"### Problem ID: {selected_problem}")
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 st.markdown(f"### {file1_name}")
#                 display_code_block(
#                     "Implementation",
#                     code1,
#                     results1_problem.get('result') == 'passed',
#                     context=results1_problem.get('context')
#                 )
            
#             with col2:
#                 st.markdown(f"### {file2_name}")
#                 display_code_block(
#                     "Implementation",
#                     code2,
#                     results2_problem.get('result') == 'passed',
#                     context=results2_problem.get('context')
#                 )
            
#             # Additional details
#             with st.expander("Show Comparison Details"):
#                 st.json({
#                     'ID': selected_problem,
#                     f'{file1_name} Result': results1_problem.get('result', 'N/A'),
#                     f'{file2_name} Result': results2_problem.get('result', 'N/A')
#                 })
            
#     except FileNotFoundError:
#         st.error("One or both comparison files not found. Please check the file paths.")
#     except Exception as e:
#         st.error(f"Error loading results: {str(e)}")
#         st.exception(e)

# if __name__ == "__main__":
#     main()

import streamlit as st
import json
from typing import Dict
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

def construct_full_code(source_code: str, problem_id: str, context_collection) -> str:
    """Construct full code by combining source code with test and entry point from MongoDB"""
    # Get context from MongoDB
    context = context_collection.find_one({'ID': problem_id})
    
    if not context:
        return "Context not found in MongoDB"
    
    typing_import = "from typing import *\n" if "from typing import *" not in source_code else ""
    
    full_code = (
        typing_import +
        source_code + "\n" +
        context['test'] + "\n" +
        f"check({context['entry_point'].strip('\"')})"
    )
    
    return full_code

def load_comparison_results(jsonl_path1: str, jsonl_path2: str) -> tuple[Dict, Dict]:
    """Load comparison results from two JSONL files."""
    results1, results2 = {}, {}
    
    with open(jsonl_path1, 'r') as f:
        for line in f:
            data = json.loads(line)
            results1[data['ID']] = data
            
    with open(jsonl_path2, 'r') as f:
        for line in f:
            data = json.loads(line)
            results2[data['ID']] = data
            
    return results1, results2

def get_divergent_cases(results1: Dict, results2: Dict) -> list:
    """Return list of problem IDs where one version passed and the other failed."""
    divergent_cases = []
    common_ids = set(results1.keys()) & set(results2.keys())
    
    for id in common_ids:
        result1 = results1[id].get('result') == 'passed'
        result2 = results2[id].get('result') == 'passed'
        
        # Only include cases where one passed and the other failed
        if result1 != result2:
            divergent_cases.append(id)
    
    return sorted(divergent_cases)

def display_code_block(title: str, code: str, is_success: bool, context: str = None):
    """Display code with improved formatting and syntax highlighting."""
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"#### {title}")
        with col2:
            if is_success:
                st.markdown('✅ Success')
            else:
                st.markdown('❌ Failed')
        
        st.code(code.strip(), language='python')
        
        st.markdown("#### Context")
        if context:
            st.markdown(context)
        else:
            st.markdown("*No Context used*")

def display_comparison(problem_id: str, results1: Dict, results2: Dict, 
                      file1_name: str, file2_name: str, context_collection):
    """Display comparison for a specific problem ID."""
    if problem_id not in results1 or problem_id not in results2:
        st.error(f"Problem ID {problem_id} not found in one or both result sets.")
        return
    
    results1_problem = results1[problem_id]
    results2_problem = results2[problem_id]
    
    # Construct full code for both versions
    code1 = construct_full_code(
        results1_problem['original_code'],
        problem_id,
        context_collection
    )
    
    code2 = construct_full_code(
        results2_problem['original_code'],
        problem_id,
        context_collection
    )
    
    st.markdown(f"### Problem ID: {problem_id}")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {file1_name}")
        display_code_block(
            "Implementation",
            code1,
            results1_problem.get('result') == 'passed',
            context=results1_problem.get('context')
        )
    
    with col2:
        st.markdown(f"### {file2_name}")
        display_code_block(
            "Implementation",
            code2,
            results2_problem.get('result') == 'passed',
            context=results2_problem.get('context')
        )
    
    with st.expander("Show Comparison Details"):
        st.json({
            'ID': problem_id,
            f'{file1_name} Result': results1_problem.get('result', 'N/A'),
            f'{file2_name} Result': results2_problem.get('result', 'N/A')
        })

def main():
    st.set_page_config(
        layout="wide",
        page_title="ExpMem Comparison Analysis",
        initial_sidebar_state="expanded"
    )
    
    file1_path = "/Users/harshavardhank/Desktop/Code/Thesis/Code/expmem/results_detail.jsonl"
    file2_path = "/Users/harshavardhank/Desktop/Code/Thesis/Code/expmem/results_mem_2.jsonl"
    file1_name = "Memory No Mem"
    file2_name = "Memory 1"
    
    db, context_collection = setup_mongodb("HumanEval", "context")
    
    st.title(f"{file1_name} vs {file2_name} Comparison")
    
    try:
        results1, results2 = load_comparison_results(file1_path, file2_path)
        
        # Get divergent cases (where one passed and other failed)
        divergent_cases = get_divergent_cases(results1, results2)
        
        # Sidebar metrics
        st.sidebar.header("Analysis Metrics")
        total_common = len(set(results1.keys()) & set(results2.keys()))
        total_divergent = len(divergent_cases)
        
        st.sidebar.metric("Total Common Cases", total_common)
        st.sidebar.metric("Pass/Fail Divergent Cases", total_divergent)
        
        # Search bar for specific problem ID
        st.sidebar.header("Search Problem")
        search_id = st.sidebar.text_input("Enter Problem ID")
        
        # Dropdown for divergent cases
        if divergent_cases:
            st.sidebar.header("Divergent Cases (Pass/Fail Different)")
            divergent_list = [(id, f"{id} ({file1_name}: {'✓' if results1[id].get('result') == 'passed' else '✗'}, " +
                             f"{file2_name}: {'✓' if results2[id].get('result') == 'passed' else '✗'})")
                            for id in divergent_cases]
            
            selected_divergent = st.sidebar.selectbox(
                "Select Divergent Case",
                [id for id, _ in divergent_list],
                format_func=lambda x: next(label for id, label in divergent_list if id == x)
            )
        else:
            st.sidebar.info("No divergent cases found (no pass/fail differences)")
            selected_divergent = None
        
        # Display results based on search or selection
        if search_id:
            display_comparison(search_id, results1, results2, file1_name, file2_name, context_collection)
        elif selected_divergent:
            display_comparison(selected_divergent, results1, results2, file1_name, file2_name, context_collection)
        
    except FileNotFoundError:
        st.error("One or both comparison files not found. Please check the file paths.")
    except Exception as e:
        st.error(f"Error loading results: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()