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

# Comparison Logic Functions
def load_expmem_results(csv_path: str) -> Dict[str, Dict]:
    """Load results and full code from Expmem (CSV) file."""
    results = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results[row['ID']] = {
                'result': row['Result'].lower() == 'true',
                'full_code': row['Full_Code'],
                'code': row.get('Code', '')  # Get the main implementation if available
            }
    return results

def load_mapcoder_results(jsonl_path: str) -> Dict[str, Dict]:
    """Load results and code components from MapCoder (JSONL) file."""
    results = {}
    with open(jsonl_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            # Extract one sample test case if available
            sample_test = None
            if data.get('sample_io'):
                sample_test = data['sample_io'][0]
            
            results[data['task_id']] = {
                'result': data['is_solved'],
                'source_code': data['source_codes'][0] if data['source_codes'] else None,
                'test': data['test'],
                'entry_point': data['entry_point'],
                'sample_test': sample_test
            }
    return results

def construct_full_mapcoder_code(data: Dict) -> str:
    """Construct full runnable code from MapCoder components."""
    code_parts = []
    
    # Add source code
    if data['source_code']:
        code_parts.append(data['source_code'])
    
    # Add test function
    if data['test']:
        code_parts.append("\n" + data['test'])
    
    # Add the check function call
    code_parts.append(f"\ncheck({data['entry_point']})")
    
    return "\n".join(code_parts)

def execute_code_safely(code: str, source: str) -> Dict:
    """Execute code in a safe environment and capture output/errors."""
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

def compare_and_execute_divergent(expmem_results: Dict[str, Dict], 
                                mapcoder_results: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    Compare results and execute code for divergent cases.
    Returns detailed execution results for analysis.
    """
    execution_results = {}
    
    # Find problems with divergent results
    common_ids = set(expmem_results.keys()) & set(mapcoder_results.keys())
    for problem_id in common_ids:
        expmem_success = expmem_results[problem_id]['result']
        mapcoder_success = mapcoder_results[problem_id]['result']
        
        if expmem_success != mapcoder_success:
            execution_results[problem_id] = {
                'expmem_claimed': expmem_success,
                'mapcoder_claimed': mapcoder_success,
                'expmem_code': expmem_results[problem_id]['code'],
                'mapcoder_code': mapcoder_results[problem_id]['source_code'],
                'sample_test': mapcoder_results[problem_id]['sample_test'],
                'expmem_execution': None,
                'mapcoder_execution': None
            }
            
            # Execute Expmem code
            expmem_code = expmem_results[problem_id]['full_code']
            expmem_execution = execute_code_safely(expmem_code, 'Expmem')
            execution_results[problem_id]['expmem_execution'] = expmem_execution
            
            # Execute MapCoder code
            mapcoder_code = construct_full_mapcoder_code(mapcoder_results[problem_id])
            mapcoder_execution = execute_code_safely(mapcoder_code, 'MapCoder')
            execution_results[problem_id]['mapcoder_execution'] = mapcoder_execution
    
    return execution_results

# Streamlit Interface Functions
def create_custom_css() -> str:
    """Create custom CSS for syntax highlighting and layout."""
    return """
    <style>
        .code-container {
            font-family: 'Courier New', Courier, monospace;
            padding: 10px;
            border-radius: 5px;
            margin: 5px;
            overflow-x: auto;
            background-color: #272822;  /* Monokai background */
        }
        .failure-background {
            border-left: 4px solid #ff6b6b;
        }
        .success-background {
            border-left: 4px solid #32CD32;
        }
        .code-header {
            font-weight: bold;
            margin-bottom: 5px;
            padding: 5px;
            border-radius: 3px;
            color: white;
            background-color: #1e1e1e;
        }
        .test-case {
            background-color: #2d2d2d;
            color: #e0e0e0;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-family: monospace;
        }
        .execution-results {
            background-color: #2d2d2d;
            color: #e0e0e0;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-family: monospace;
            white-space: pre-wrap;
        }
        .error-message {
            color: #ff6b6b;
            margin-top: 5px;
        }
        .success-message {
            color: #32CD32;
            margin-top: 5px;
        }
        .stButton>button {
            width: 100%;
        }
        """ + HtmlFormatter(style='monokai').get_style_defs('.highlight')

def create_highlighted_code(code: str, is_success: bool) -> str:
    """Create HTML for syntax-highlighted code with background based on success."""
    highlighted = highlight(code, PythonLexer(), HtmlFormatter(style='monokai'))
    background_class = 'success-background' if is_success else 'failure-background'
    
    return f"""
    <div class='code-container {background_class}'>
        {highlighted}
    </div>
    """

def display_execution_results(execution_result: Dict):
    """Display execution results in a formatted way."""
    st.markdown("<div class='execution-results'>", unsafe_allow_html=True)
    
    # Display success/failure status
    status_class = 'success-message' if execution_result['success'] else 'error-message'
    st.markdown(f"<div class='{status_class}'>Status: {'✓ Success' if execution_result['success'] else '✗ Failed'}</div>",
                unsafe_allow_html=True)
    
    # Display output if any
    if execution_result['output']:
        st.markdown("**Output:**")
        st.code(execution_result['output'].strip(), language='text')
    
    # Display error if any
    if execution_result['error']:
        st.markdown("**Error:**")
        st.markdown(f"<div class='error-message'>{execution_result['error']}</div>",
                    unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    st.set_page_config(
        layout="wide", 
        page_title="Code Comparison Analysis",
        initial_sidebar_state="expanded"
    )
    
    st.title("MapCoder vs Expmem Code Comparison")
    
    # Apply custom CSS
    st.markdown(create_custom_css(), unsafe_allow_html=True)
    
    # File uploader section
    st.sidebar.header("Upload Files")
    csv_file = st.sidebar.file_uploader("Upload Expmem CSV file", type=['csv'])
    jsonl_file = st.sidebar.file_uploader("Upload MapCoder JSONL file", type=['jsonl'])
    
    if csv_file and jsonl_file:
        # Save uploaded files temporarily
        with open('temp.csv', 'wb') as f:
            f.write(csv_file.getvalue())
        with open('temp.jsonl', 'wb') as f:
            f.write(jsonl_file.getvalue())
        
        try:
            # Load results using comparison logic
            expmem_results = load_expmem_results('temp.csv')
            mapcoder_results = load_mapcoder_results('temp.jsonl')
            
            # Get divergent results
            execution_results = compare_and_execute_divergent(expmem_results, mapcoder_results)
            
            # Display metrics
            st.sidebar.header("Analysis Metrics")
            st.sidebar.metric("Total Problems", len(expmem_results))
            st.sidebar.metric("Divergent Cases", len(execution_results))
            divergence_rate = len(execution_results)/len(expmem_results)*100
            st.sidebar.metric("Divergence Rate", f"{divergence_rate:.1f}%")
            
            # Problem selector
            st.sidebar.header("Problem Selection")
            divergent_cases = list(execution_results.keys())
            selected_problem = st.sidebar.selectbox(
                "Select Problem ID",
                divergent_cases,
                format_func=lambda x: (
                    f"{x} (MapCoder: {'✓' if execution_results[x]['mapcoder_claimed'] else '✗'}, "
                    f"Expmem: {'✓' if execution_results[x]['expmem_claimed'] else '✗'})"
                )
            )
            
            if selected_problem:
                problem_results = execution_results[selected_problem]
                
                # Create two columns for side-by-side comparison
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(
                        f"<h3>MapCoder Implementation {'✓' if problem_results['mapcoder_claimed'] else '✗'}</h3>",
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        create_highlighted_code(
                            problem_results['mapcoder_code'],
                            problem_results['mapcoder_claimed']
                        ),
                        unsafe_allow_html=True
                    )
                    
                    st.markdown("### Execution Results")
                    display_execution_results(problem_results['mapcoder_execution'])
                    
                    if problem_results['sample_test']:
                        st.markdown("### Sample Test Case")
                        st.markdown(
                            f"""<div class='test-case'>{problem_results['sample_test']}</div>""",
                            unsafe_allow_html=True
                        )
                
                with col2:
                    st.markdown(
                        f"<h3>Expmem Implementation {'✓' if problem_results['expmem_claimed'] else '✗'}</h3>",
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        create_highlighted_code(
                            problem_results['expmem_code'],
                            problem_results['expmem_claimed']
                        ),
                        unsafe_allow_html=True
                    )
                    
                    st.markdown("### Execution Results")
                    display_execution_results(problem_results['expmem_execution'])
                
        except Exception as e:
            st.error(f"Error processing files: {str(e)}")
            st.exception(e)
    else:
        st.info("Please upload both CSV and JSONL files to begin analysis.")

if __name__ == "__main__":
    main()