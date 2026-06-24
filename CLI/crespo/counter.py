import tiktoken
from . import cli
import sys

def tok_count(valid,out):
    if not out:
        print("Error: Output File not Generated")
        return 0,0
    counter = tiktoken.get_encoding("o200k_base")

    total =0
    for file in valid:
        with open(file["abspath"],"r",encoding="utf8",errors="ignore") as f:
            content = f.read()
        total+=len(counter.encode(content))

    try:
        with open(str(out),"r",encoding="utf8",errors="ignore") as o:
            outcontent = o.read()
        outtok = len(counter.encode(outcontent))
    except FileNotFoundError:
        cli.print_error("Output File not found")
        return total,0

    return total,outtok