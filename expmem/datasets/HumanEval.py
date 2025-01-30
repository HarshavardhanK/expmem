
from expmem.datasets.Dataset import Dataset
from expmem.constants.paths import HUMAN_WST_DATA_PATH

from dspy.datasets import DataLoader

class HumanEval(Dataset):

    def __init__(
            self,
            path: str = HUMAN_WST_DATA_PATH
    ):
        super().__init__(path)
        self._id = "task_id"
        self._path = path

    def load_data(self):

        dataloader = DataLoader()

        jsonl_dataset = dataloader.from_json(
            file_path=self._path,
            fields=("task_id", "prompt", "canonical_solution", "entry_point", "test", "sample_io"),
            input_keys=("prompt")
        )

        return jsonl_dataset
    
if __name__ == '__main__':
    dataset = HumanEval()
    
    for q in dataset:
        print(q.prompt)


