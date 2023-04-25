import json
import re

class CollectionsManager:
    """
    Circular queue class that stores max_collections most-recent items
    """
    def __init__(self, max_collections, init_value=None):
        self.max_collections=max_collections
        self.cq_idx=0
        self.init_value=init_value
        self.cq_collections = [self.init_value for _ in range(max_collections)]
    
    def clear(self):
        self.cq_collections = [self.init_value for _ in range(self.max_collections)]
        self.cq_idx=0

    def is_new(self, value):
        return value not in self.cq_collections
    
    def add_collection(self, value, check_new=False):
        if check_new and not self.is_new(value):
            return
        self.cq_collections[self.cq_idx] = value
        self.cq_idx = (self.cq_idx + 1) % self.max_collections

    def write(self, filename, sep="\n"):
        idx = self.cq_idx
        with open(filename, "w") as fw:
            for i in range(self.max_collections):
                writable = self.cq_collections[idx]
                if str(writable)==str(self.init_value):
                    continue
                fw.write("{}{}".format(writable, sep))
                idx = (idx + 1) % self.max_collections

def load_config(file):
    with open(file, 'r') as fr:
        data = json.load(fr)
    return data

def get_hash(string):
    s = '_'.join(re.findall('\w+', string))
    return s