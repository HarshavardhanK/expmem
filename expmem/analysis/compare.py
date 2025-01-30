import streamlit as st
import json
import csv
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from typing import Dict, Set, Tuple
import sys
from io import StringIO
import traceback
from collections import defaultdict

# Comparison Logic Functions remain the same as before
def load_expmem_results(csv_path: str) -> Dict[str, Dict]:
    """Load results and full code from Expmem (CSV) file."""
    results = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results[row['ID']] = {
                'result': row['Result'].lower() == 'true',
                'full_code': row['Full_Code'],
                'code': row.get('Code', '')
            }
    return results

def load_mapcoder_results(jsonl_path: str) -> Dict[str, Dict]:
    """Load results and code components from MapCoder (JSONL) file."""
    results = {}
    with open(jsonl_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            sample_test = None
            if data.get('sample_io'):
                sample_test = data['sample_io'][0]
            
            results[data['task_id']] = {
                'result': data['is_solved'],
                'source_codes': data['source_codes'][0] if data['source_codes'] else None,
                'test': data['test'],
                'entry_point': data['entry_point'],
                'sample_test': sample_test,
                'full_code': construct_full_mapcoder_code(data) if data['source_codes'] else None
            }
    return results

def construct_full_mapcoder_code(data: Dict) -> str:
    """Construct full runnable code from MapCoder components."""
    code_parts = []
    if data['source_codes']:
        code_parts.append(data['source_codes'][0])
    if data['test']:
        code_parts.append("\n" + data['test'])
    code_parts.append(f"\ncheck({data['entry_point']})")
    return "\n".join(code_parts)

def compare_and_execute_divergent(expmem_results: Dict[str, Dict], 
                                mapcoder_results: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    Compare results between Expmem and MapCoder implementations and execute code for divergent cases.
    
    Args:
        expmem_results (Dict[str, Dict]): Results from Expmem, containing code and success status
        mapcoder_results (Dict[str, Dict]): Results from MapCoder, containing code and success status
    
    Returns:
        Dict[str, Dict]: Dictionary containing detailed execution results for divergent cases
    """
    execution_results = {}
    
    # Find problems with divergent results
    common_ids = set(expmem_results.keys()) & set(mapcoder_results.keys())
    
    for problem_id in common_ids:
        expmem_success = expmem_results[problem_id]['result']
        mapcoder_success = mapcoder_results[problem_id]['result']
        
        # Only process cases where results differ
        if expmem_success != mapcoder_success:
            execution_results[problem_id] = {
                # Store claimed results
                'expmem_claimed': expmem_success,
                'mapcoder_claimed': mapcoder_success,
                
                # Store code implementations
                'expmem_code': expmem_results[problem_id]['code'],
                'mapcoder_code': mapcoder_results[problem_id]['source_codes'],
                
                # Store sample test if available
                'sample_test': mapcoder_results[problem_id].get('sample_test'),
                
                # Placeholders for execution results
                'expmem_execution': None,
                'mapcoder_execution': None
            }
            
            # Execute Expmem code
            try:
                expmem_code = expmem_results[problem_id]['full_code']
                expmem_execution = execute_code_safely(expmem_code, 'Expmem')
                execution_results[problem_id]['expmem_execution'] = expmem_execution
            except Exception as e:
                execution_results[problem_id]['expmem_execution'] = {
                    'success': False,
                    'error': f"Failed to execute Expmem code: {str(e)}",
                    'exception_type': type(e).__name__,
                    'output': ''
                }
            
            # Execute MapCoder code
            try:
                mapcoder_code = construct_full_mapcoder_code(mapcoder_results[problem_id])
                mapcoder_execution = execute_code_safely(mapcoder_code, 'MapCoder')
                execution_results[problem_id]['mapcoder_execution'] = mapcoder_execution
            except Exception as e:
                execution_results[problem_id]['mapcoder_execution'] = {
                    'success': False,
                    'error': f"Failed to construct or execute MapCoder code: {str(e)}",
                    'exception_type': type(e).__name__,
                    'output': ''
                }
            
            # Add additional metadata
            execution_results[problem_id]['analysis'] = {
                'execution_match': (
                    execution_results[problem_id]['expmem_execution']['success'] ==
                    execution_results[problem_id]['mapcoder_execution']['success']
                ),
                'output_match': (
                    execution_results[problem_id]['expmem_execution'].get('output', '').strip() ==
                    execution_results[problem_id]['mapcoder_execution'].get('output', '').strip()
                ),
                'both_failed': (
                    not execution_results[problem_id]['expmem_execution']['success'] and
                    not execution_results[problem_id]['mapcoder_execution']['success']
                ),
                'both_succeeded': (
                    execution_results[problem_id]['expmem_execution']['success'] and
                    execution_results[problem_id]['mapcoder_execution']['success']
                )
            }
    
    return execution_results

def execute_code_safely(code: str, source: str) -> Dict:
    """
    Execute code in a safe environment and capture output/errors.
    
    Args:
        code (str): The code to execute
        source (str): Source identifier for error messages
    
    Returns:
        Dict: Execution results containing success status, output, and any errors
    """
    result = {
        'success': False,
        'output': '',
        'error': '',
        'exception_type': None
    }
    
    # Create string buffer to capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        # Create a new namespace to avoid global namespace pollution
        namespace = {}
        exec(code, namespace)
        result['success'] = True
        
    except Exception as e:
        result['error'] = traceback.format_exc()
        result['exception_type'] = type(e).__name__
        
    finally:
        # Capture output and restore stdout
        result['output'] = sys.stdout.getvalue()
        sys.stdout = old_stdout
    
    return result

def strip_html_tags(code: str) -> str:
    """Remove HTML tags and decode HTML entities from code string."""
    import re
    from html import unescape
    
    # Remove HTML tags
    clean_code = re.sub(r'<[^>]+>', '', code)
    # Decode HTML entities
    clean_code = unescape(clean_code)
    # Fix any mangled whitespace
    clean_code = clean_code.replace('&nbsp;', ' ')
    return clean_code


def display_code_block(title: str, code: str, is_success: bool, show_full_code: bool = True):
    """Display code with improved formatting and syntax highlighting using Streamlit's native capabilities."""
    # Clean the code
    cleaned_code = strip_html_tags(code)
    
    # Create container for the code block
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
        
        # Display code using Streamlit's native code display
        st.code(cleaned_code, language='python')

def display_execution_results(execution_result: Dict):
    """Display execution results using Streamlit's native components."""
    with st.container():
        st.markdown("#### Execution Results")
        
        # Status
        if execution_result['success']:
            st.success('✅ Execution Successful')
        else:
            st.error('❌ Execution Failed')
        
        # Output
        if execution_result['output']:
            st.markdown("**Output:**")
            st.code(execution_result['output'].strip(), language='python')
        
        # Error
        if execution_result['error']:
            st.markdown("**Error:**")
            st.code(execution_result['error'], language='python')
            
def main():
    st.set_page_config(
        layout="wide",
        page_title="Code Comparison Analysis",
        initial_sidebar_state="expanded"
    )
    
    st.title("MapCoder vs Expmem Code Comparison")
    
    # File upload section
    st.sidebar.header("Upload Files")
    csv_file = st.sidebar.file_uploader("Upload Expmem CSV file", type=['csv'])
    jsonl_file = st.sidebar.file_uploader("Upload MapCoder JSONL file", type=['jsonl'])
    
    # View options
    st.sidebar.header("View Options")
    show_full_code = st.sidebar.checkbox("Show Full Code", value=True)
    
    if csv_file and jsonl_file:
        # Save uploaded files
        with open('temp.csv', 'wb') as f:
            f.write(csv_file.getvalue())
        with open('temp.jsonl', 'wb') as f:
            f.write(jsonl_file.getvalue())
        
        try:
            # Load and process results
            expmem_results = load_expmem_results('temp.csv')
            mapcoder_results = load_mapcoder_results('temp.jsonl')
            execution_results = compare_and_execute_divergent(expmem_results, mapcoder_results)
            
            # Display metrics
            st.sidebar.header("Analysis Metrics")
            col1, col2, col3 = st.sidebar.columns(3)
            col1.metric("Total Problems", len(expmem_results))
            col2.metric("Divergent Cases", len(execution_results))
            col3.metric("Divergence Rate", f"{(len(execution_results)/len(expmem_results)*100):.1f}%")
            
            # Problem selection
            st.sidebar.header("Problem Selection")
            problem_list = [(id, f"{id} (MC: {'✓' if execution_results[id]['mapcoder_claimed'] else '✗'}, " +
                           f"EX: {'✓' if execution_results[id]['expmem_claimed'] else '✗'})")
                           for id in execution_results.keys()]
            
            selected_problem = st.sidebar.selectbox(
                "Select Problem ID",
                [id for id, _ in problem_list],
                format_func=lambda x: next(label for id, label in problem_list if id == x)
            )
            
            if selected_problem:
                problem_results = execution_results[selected_problem]
                
                # Create columns for side-by-side comparison
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### MapCoder Implementation")
                    code_to_show = (mapcoder_results[selected_problem]['full_code'] 
                                  if show_full_code 
                                  else problem_results['mapcoder_code'])
                    display_code_block(
                        "Implementation",
                        code_to_show,
                        problem_results['mapcoder_claimed']
                    )
                    display_execution_results(problem_results['mapcoder_execution'])
                    
                    if problem_results['sample_test']:
                        st.markdown("### Sample Test Case")
                        st.code(strip_html_tags(problem_results['sample_test']), language='python')
                
                with col2:
                    st.markdown("### Expmem Implementation")
                    code_to_show = (expmem_results[selected_problem]['full_code']
                                  if show_full_code
                                  else problem_results['expmem_code'])
                    display_code_block(
                        "Implementation",
                        code_to_show,
                        problem_results['expmem_claimed']
                    )
                    display_execution_results(problem_results['expmem_execution'])
        
        except Exception as e:
            st.error(f"Error processing files: {str(e)}")
            st.exception(e)
    else:
        st.info("Please upload both CSV and JSONL files to begin analysis.")

if __name__ == "__main__":
    main()