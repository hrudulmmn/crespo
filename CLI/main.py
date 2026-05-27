import argparse
import os
import walker
import parse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        prog="knowgit",description="Know your codebase"
    )

    parser.add_argument("path",type=str,help="the root directory path of your codebase")

    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Error: Specified Path({args.path}) Does not Exist!")
        return
    
    valid_files = walker.walk_dir(path=args.path)
    extracted=[]
    for file in valid_files:
        signature = parse.extract(Path(file["abspath"]).resolve(),file["relpath"])
        extracted.append(signature)
    print(extracted)
    

if __name__=="__main__":
    main()