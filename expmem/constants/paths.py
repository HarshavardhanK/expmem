import os
from os.path import join, dirname

EXPMEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the path to the data directory
DATA_DIR = os.path.join(EXPMEM_DIR, 'data')

# HumanEval Dataset
HUMAN_WST_DATA_PATH = os.path.join(DATA_DIR, 'HumanEvalWST.jsonl')

#MBPP Dataset
MBPP_DATA_PATH = os.path.join(DATA_DIR, 'mbpp-py.jsonl')