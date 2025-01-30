
class Dataset(object):

    def __init__(self, path: str):
        self._path = path
        self._data = self.load_data()
        self._len = len(self._data)
        self._id = None

    def load_data(self):
        raise NotImplementedError("Subclasses must implement load_data method")
    
    def __getitem__(self, idx):
        return self._data[idx]
    
    def __len__(self):
        return self._len
