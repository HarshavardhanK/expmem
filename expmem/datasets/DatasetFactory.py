from expmem.datasets.HumanEval import HumanEval
from expmem.datasets.MBPP import MBPP

class DatasetFactory(object):
    def __init__(self, dataset_name: str):
        self.dataset_name = dataset_name

    def get_dataset(self):
        if self.dataset_name == "HumanEval":
            return HumanEval()
        
        elif self.dataset_name == "MBPP":
            return MBPP()
        else:
            raise ValueError(f"Dataset {self.dataset_name} not found")

    