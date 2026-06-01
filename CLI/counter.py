import tiktoken

def tok_count(valid,out):
    if not out:
        print("Error: Output File not Generated")
        return
    counter = tiktoken.get_encoding("o200k_base")

    total =0
    for file in valid:
        with open(file["abspath"],"r",encoding="utf8") as f:
            content = f.read()
        total+=len(counter.encode(content))

    with open(str(out),"r",encoding="utf8") as o:
        outcontent = o.read()
    outtok = len(counter.encode(outcontent))

    print("Token for Original File:",total)
    print("Token for Output File:",outtok)