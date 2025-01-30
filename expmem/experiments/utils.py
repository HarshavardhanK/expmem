import pandas as pd
import os

import re

def extract_python_code(text):
    """
    Extracts the first Python code block from text that uses triple backtick markers.
    Returns the extracted code as a string, or None if no code block is found.
    """
    pattern = r"```python\n((?:(?!```).|\n)+)```"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None

def setup_csv(filename='result_test.csv'):
    """Initialize CSV file with headers if it doesn't exist"""
    columns = ['ID', 'Error Analysis', 'Summary Explanation', 'Detailed Explanation', 'Result', 'Prompt', 'Code', 'Test', 'Full_Code', 'Context']
    if not os.path.exists(filename):
        pd.DataFrame(columns=columns).to_csv(filename, index=False)

def append_result(data, ID, code, exec_res, summary, detailed, filename='result_test.csv'):
    """Append a single result to the CSV file"""
    result_row = {
        'ID': data[ID],
        'Error Ananlysis': exec_res['prediction'],
        'Summary Explanation': summary,
        'Detailed Explanation': detailed,
        'Result': exec_res['result'],
        'Prompt': data.prompt,
        'Code': code,
        'Test': str(data.test),  # Convert to string to ensure it can be stored in CSV
        "Full_Code": exec_res['full_code'],
        'Context': exec_res.get('context', None)
    }
    
    pd.DataFrame([result_row]).to_csv(filename, mode='a', header=False, index=False)
    return result_row

