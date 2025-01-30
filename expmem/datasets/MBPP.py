
from expmem.datasets.Dataset import Dataset
from expmem.constants.paths import MBPP_DATA_PATH

from dspy.datasets import DataLoader

class MBPP(Dataset):

    def __init__(
            self,
            path: str = MBPP_DATA_PATH
    ):
        super().__init__(path)
        self._id = "name"
        self._path = path

    def load_data(self):

        dataloader = DataLoader()

        jsonl_dataset = dataloader.from_json(
            file_path=self._path,
            fields=("name", "prompt", "language", "entry_point", "test", "sample_io"),
            input_keys=("prompt")
        )

        return jsonl_dataset
    
if __name__ == '__main__':
    dataset = MBPP()
    
    for q in dataset:
        print(q.prompt)


