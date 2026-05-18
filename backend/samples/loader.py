import os
from typing import List

def load_sample_xml(is_valid: bool = True) -> List[bytes]:
    folder = "samples/valid" if is_valid else "samples/invalid"
    files = []
    if not os.path.exists(folder):
        return files
        
    for filename in os.listdir(folder):
        if filename.endswith(".xml"):
            with open(os.path.join(folder, filename), "rb") as f:
                files.append(f.read())
    return files
