import argparse
import os
import walker

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
    

if __name__=="__main__":
    main()