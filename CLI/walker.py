import os
from pathlib import Path
import config

def walk_dir(path:str):
    IGNORE_FOLDERS = {'.git', 'node_modules', '__pycache__', '.next', 'venv', '.venv'}
    IGNORE_FILES = {'package-lock.json', 'yarn.lock', '.DS_Store','.gitignore'}
    CONFIG_FILES = {
    "package.json", "requirements.txt",
    "Cargo.toml", "go.mod", "Dockerfile"
    }

    print(f"\nDirectory walking started!")
    print(f"\n Walking Directory: {path}")

    file_count=0
    valid_files=[]

    base_path = Path(path).resolve()
    for root,dirs,files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS ]

        for file in files:
            isconfig = False
            if file in IGNORE_FILES:
                continue
            if file in CONFIG_FILES:
                isconfig=True
            if not isconfig and (Path(file)).suffix.lower() not in config.get_config():
                continue

            full_path = os.path.join(root,file)
            file_count+=1
            print(f"Valid File Found: {full_path}")
            valid_files.append({"abspath":full_path,"relpath":str(Path(full_path).resolve().relative_to(base_path)),"isconfig":isconfig})

    print("-"*60)
    print(f"Scan Completed Found {file_count} Valid Files!")

    return valid_files