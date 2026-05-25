import os


def walk_dir(path:str):
    IGNORE_FOLDERS = {'.git', 'node_modules', '__pycache__', '.next', 'venv', '.venv'}
    IGNORE_FILES = {'package-lock.json', 'yarn.lock', '.DS_Store'}

    print(f"\nDirectory walking started!")
    print(f"\n Walking Directory: {path}")

    file_count=0
    valid_files=[]

    for root,dirs,files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS ]

        for file in files:
            if file in IGNORE_FILES:
                continue

            full_path = os.path.join(root,file)
            file_count+=1
            print(f"Valid File Found: {full_path}")
            valid_files.append(full_path)

    print("-"*60)
    print(f"Scan Completed Found {file_count} Valid Files!")

    return valid_files