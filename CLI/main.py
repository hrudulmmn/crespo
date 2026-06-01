import argparse
import os
import walker
import parse
import generate
import counter
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        prog="crespo",description="Know your codebase"
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("path",type=str,help="the root directory path of your codebase")
    group.add_argument("--git",help="GitHub URL for required repo")
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

    out_path=None

    if mode=="structure":
        out_path=generate.gen_struct(extracted,reponame)
    elif mode=="summarize":
        out_path=generate.gen_summ(extracted,reponame)
    elif mode=="concat":
        out_path = generate.gen_concat(valid_files,reponame=reponame)

    counter.tok_count(valid_files,out_path)

    

if __name__=="__main__":
    main()