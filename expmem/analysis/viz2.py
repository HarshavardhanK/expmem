# # import streamlit as st
# # import json
# # from typing import Dict
# # from pymongo import MongoClient
# # from pymongo.server_api import ServerApi
# # import os

# # def setup_mongodb(database: str, collection: str) -> tuple:
# #     mongodb_uri = os.getenv("MONGODB_URI")
# #     client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
    
# #     db = client[database]
# #     coll = db[collection]
    
# #     return db, coll

# # def load_comparison_results(jsonl_path: str) -> Dict:
# #     """Load comparison results from JSONL file."""
# #     results = {}
# #     with open(jsonl_path, 'r') as f:
# #         for line in f:
# #             data = json.loads(line)
# #             results[data['ID']] = data
# #     return results

# # def strip_html_tags(code: str) -> str:
# #     """Remove HTML tags and decode HTML entities from code string."""
# #     import re
# #     from html import unescape
    
# #     clean_code = re.sub(r'<[^>]+>', '', code)
# #     clean_code = unescape(clean_code)
# #     clean_code = clean_code.replace('&nbsp;', ' ')
# #     return clean_code

# # def display_code_block(title: str, code: str, is_success: bool, context: str = None):
# #     """Display code with improved formatting and syntax highlighting."""
# #     with st.container():
# #         # Header with status
# #         col1, col2 = st.columns([3, 1])
# #         with col1:
# #             st.markdown(f"#### {title}")
# #         with col2:
# #             if is_success:
# #                 st.markdown('✅ Success')
# #             else:
# #                 st.markdown('❌ Failed')
        
# #         # Display code
# #         st.code(strip_html_tags(code), language='python')
        
# #         # Display context if available
# #         if context:
# #             st.markdown("#### Context")
# #             st.markdown("```python")
# #             st.markdown(strip_html_tags(context))
# #             st.markdown("```")

# # def main():
# #     st.set_page_config(
# #         layout="wide",
# #         page_title="Code Comparison Analysis",
# #         initial_sidebar_state="expanded"
# #     )
    
# #     st.title("ExpMem vs MapCoder Code Comparison")
    
# #     # Load comparison results
# #     try:
# #         results = load_comparison_results("/Users/harshavardhank/Desktop/Code/Thesis/Code/expmem/mapcoder_naive_mem_2_comparison.jsonl")
        
# #         # Display metrics
# #         st.sidebar.header("Analysis Metrics")
# #         total_divergent = len(results)
# #         st.sidebar.metric("Divergent Cases", total_divergent)
        
# #         # Problem selection
# #         st.sidebar.header("Problem Selection")
# #         problem_list = [(id, f"{id} (MC: {'✓' if results[id]['mapcoder_passed'] else '✗'}, " +
# #                         f"EX: {'✓' if results[id]['expmem_passed'] else '✗'})")
# #                        for id in results.keys()]
        
# #         selected_problem = st.sidebar.selectbox(
# #             "Select Problem ID",
# #             [id for id, _ in problem_list],
# #             format_func=lambda x: next(label for id, label in problem_list if id == x)
# #         )
        
# #         if selected_problem:
# #             problem_results = results[selected_problem]
            
# #             # Create columns for side-by-side comparison
# #             col1, col2 = st.columns(2)
            
# #             with col1:
# #                 st.markdown("### ExpMem Implementation")
# #                 display_code_block(
# #                     "Implementation",
# #                     problem_results['expmem_fullcode'],
# #                     problem_results['expmem_passed'],
# #                     context=problem_results.get('context')  # Pass context to display
# #                 )
                
# #                 print(problem_results['expmem_fullcode'])
            
# #             with col2:
# #                 st.markdown("### MapCoder Implementation")
# #                 display_code_block(
# #                     "Implementation",
# #                     problem_results['mapcoder_fullcode'],
# #                     problem_results['mapcoder_passed']
# #                 )
            
# #             # Additional details
# #             with st.expander("Show Comparison Details"):
# #                 st.json({
# #                     'ID': selected_problem,
# #                     'ExpMem Passed': problem_results['expmem_passed'],
# #                     'MapCoder Passed': problem_results['mapcoder_passed']
# #                 })
            
# #     except FileNotFoundError:
# #         st.error("Comparison results file not found. Please run the comparison script first.")
# #     except Exception as e:
# #         st.error(f"Error loading results: {str(e)}")
# #         st.exception(e)

# # if __name__ == "__main__":
# #     main()

# import streamlit as st
# import json
# from typing import Dict
# from pymongo import MongoClient
# from pymongo.server_api import ServerApi
# import os

# def setup_mongodb(database: str, collection: str) -> tuple:
#     mongodb_uri = os.getenv("MONGODB_URI")
#     client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
    
#     db = client[database]
#     coll = db[collection]
    
#     return db, coll

# def load_comparison_results(jsonl_path: str) -> Dict:
#     """Load comparison results from JSONL file."""
#     results = {}
#     with open(jsonl_path, 'r') as f:
#         for line in f:
#             data = json.loads(line)
#             results[data['ID']] = data
#     return results

# def clean_code(code: str) -> str:
#     """Clean and format code while preserving its structure."""
#     # Split the code at the check function if it exists
#     if 'def check(' in code:
#         code = code.split('def check(')[0].strip()
    
#     # Remove any trailing whitespace
#     return code.strip()

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
        
#         # Display code
#         cleaned_code = clean_code(code)
#         st.code(cleaned_code, language='python')
        
#         # Display context if available
#         if context:
#             st.markdown("#### Context")
#             st.markdown(context)

# def main():
#     st.set_page_config(
#         layout="wide",
#         page_title="Code Comparison Analysis",
#         initial_sidebar_state="expanded"
#     )
    
#     st.title("ExpMem vs MapCoder Code Comparison")
    
#     # Load comparison results
#     try:
#         results = load_comparison_results("/Users/harshavardhank/Desktop/Code/Thesis/Code/expmem/mapcoder_naive_mem_2_comparison.jsonl")
        
#         # Display metrics
#         st.sidebar.header("Analysis Metrics")
#         total_divergent = len(results)
#         st.sidebar.metric("Divergent Cases", total_divergent)
        
#         # Problem selection
#         st.sidebar.header("Problem Selection")
#         problem_list = [(id, f"{id} (MC: {'✓' if results[id]['mapcoder_passed'] else '✗'}, " +
#                         f"EX: {'✓' if results[id]['expmem_passed'] else '✗'})")
#                        for id in results.keys()]
        
#         selected_problem = st.sidebar.selectbox(
#             "Select Problem ID",
#             [id for id, _ in problem_list],
#             format_func=lambda x: next(label for id, label in problem_list if id == x)
#         )
        
#         if selected_problem:
#             problem_results = results[selected_problem]
            
#             # Create columns for side-by-side comparison
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 st.markdown("### ExpMem Implementation")
#                 display_code_block(
#                     "Implementation",
#                     problem_results['expmem_fullcode'],
#                     problem_results['expmem_passed'],
#                     context=problem_results.get('context')
#                 )
            
#             with col2:
#                 st.markdown("### MapCoder Implementation")
#                 display_code_block(
#                     "Implementation",
#                     problem_results['mapcoder_fullcode'],
#                     problem_results['mapcoder_passed']
#                 )
            
#             # Additional details
#             with st.expander("Show Comparison Details"):
#                 st.json({
#                     'ID': selected_problem,
#                     'ExpMem Passed': problem_results['expmem_passed'],
#                     'MapCoder Passed': problem_results['mapcoder_passed']
#                 })
            
#     except FileNotFoundError:
#         st.error("Comparison results file not found. Please run the comparison script first.")
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

def setup_mongodb(database: str, collection: str) -> tuple:
    mongodb_uri = os.getenv("MONGODB_URI")
    client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
    
    db = client[database]
    coll = db[collection]
    
    return db, coll

def load_comparison_results(jsonl_path: str) -> Dict:
    """Load comparison results from JSONL file."""
    results = {}
    with open(jsonl_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            results[data['ID']] = data
    return results

def display_code_block(title: str, code: str, is_success: bool, context: str = None):
    """Display code with improved formatting and syntax highlighting."""
    with st.container():
        # Header with status
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"#### {title}")
        with col2:
            if is_success:
                st.markdown('✅ Success')
            else:
                st.markdown('❌ Failed')
        
        # Display full code without any processing
        st.code(code.strip(), language='python')
        
        # Display context if available
        if context:
            st.markdown("#### Context")
            st.markdown(context)

def main():
    st.set_page_config(
        layout="wide",
        page_title="Code Comparison Analysis",
        initial_sidebar_state="expanded"
    )
    
    st.title("ExpMem vs MapCoder Code Comparison")
    
    # Load comparison results
    try:
        results = load_comparison_results("/Users/harshavardhank/Desktop/Code/Thesis/Code/expmem/mapcoder_mem_128_comparison.jsonl")
        
        # Display metrics
        st.sidebar.header("Analysis Metrics")
        total_divergent = len(results)
        st.sidebar.metric("Divergent Cases", total_divergent)
        
        # Problem selection
        st.sidebar.header("Problem Selection")
        problem_list = [(id, f"{id} (MC: {'✓' if results[id]['mapcoder_passed'] else '✗'}, " +
                        f"EX: {'✓' if results[id]['expmem_passed'] else '✗'})")
                       for id in results.keys()]
        
        selected_problem = st.sidebar.selectbox(
            "Select Problem ID",
            [id for id, _ in problem_list],
            format_func=lambda x: next(label for id, label in problem_list if id == x)
        )
        
        if selected_problem:
            problem_results = results[selected_problem]
            
            # Create columns for side-by-side comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ExpMem Implementation")
                display_code_block(
                    "Implementation",
                    problem_results['expmem_fullcode'],
                    problem_results['expmem_passed'],
                    context=problem_results.get('context')
                )
            
            with col2:
                st.markdown("### MapCoder Implementation")
                display_code_block(
                    "Implementation",
                    problem_results['mapcoder_fullcode'],
                    problem_results['mapcoder_passed']
                )
            
            # Additional details
            with st.expander("Show Comparison Details"):
                st.json({
                    'ID': selected_problem,
                    'ExpMem Passed': problem_results['expmem_passed'],
                    'MapCoder Passed': problem_results['mapcoder_passed']
                })
            
    except FileNotFoundError:
        st.error("Comparison results file not found. Please run the comparison script first.")
    except Exception as e:
        st.error(f"Error loading results: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()