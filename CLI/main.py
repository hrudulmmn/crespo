import argparse
import os
import walker
import parse
import generate
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        prog="crespo",description="Know your codebase"
    )

    mode = "structure"
    parser.add_argument("path",type=str,help="the root directory path of your codebase")
    parser.add_argument("--mode",choices=["structure","summarize","concat"],default="structure",help="Select Mode for Output")

    args = parser.parse_args()
    path = args.path
    reponame = Path(path).resolve().name

    mode = args.mode
        

    print(reponame)
    if not os.path.exists(args.path):
        print(f"Error: Specified Path({args.path}) Does not Exist!")
        return
    
    valid_files = walker.walk_dir(path=args.path)

    extracted=[]
    for file in valid_files:
        signature = parse.extract_struct(Path(file["abspath"]).resolve(),mode,file["relpath"])
        extracted.append(signature)
    print(extracted)

    if mode=="structure":
        generate.gen_struct(extracted,reponame)
    elif mode=="summarize":
        generate.gen_summ(extracted,reponame)

    

if __name__=="__main__":
    main()