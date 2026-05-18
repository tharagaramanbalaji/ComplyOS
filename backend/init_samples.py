import os

def create_sample_dirs():
    dirs = [
        "samples",
        "samples/valid",
        "samples/invalid"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"Created {d}")

    # Create loader logic placeholder
    loader_content = """import os
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
"""
    with open("samples/loader.py", "w") as f:
        f.write(loader_content)
    print("Created loader.py")

if __name__ == "__main__":
    create_sample_dirs()
