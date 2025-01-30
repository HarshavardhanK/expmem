from dspy.datasets import DataLoader

def load_jsonl(file_path: str):

    dataloader = DataLoader()

    jsonl_dataset = dataloader.from_json(
        file_path=file_path,
        fields=("task_id", "prompt", "cannonical_solution", "entry_point", "test", "sample_io"),
        input_keys=("prompt")
    )

    return jsonl_dataset