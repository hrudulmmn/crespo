import xml.etree.ElementTree as ET
import sys
import os
from pathlib import Path
from .summary import Summariser
from . import security

def is_stdlib(module):
    
    return module in sys.stdlib_module_names

def _out_path(filename):
    return  Path(os.getcwd())/filename

def _clean_import(im: str) -> str:
    im = im.strip().strip("'\"")
    if not im:
        return ""
    # relative path → use stem
    if im.startswith("."):
        return Path(im).stem
    # scoped package → keep as-is e.g. @clerk/clerk-react → clerk-react
    if im.startswith("@"):
        parts = im.lstrip("@").split("/")
        return parts[1] if len(parts) > 1 else parts[0]
    # normal package → first segment e.g. react-dom/client → react-dom
    return im.split("/")[0]   

def gen_struct(extracted,reponame):
    root = ET.Element("repo",{"n":str(reponame)})
    meta = ET.SubElement(root,"meta")
    deps = ET.SubElement(meta,"dep")
    imports=[]
    pathstem=[]


    for file in extracted:
        if file.get('Fallback'):
            continue
        pathstem.append(Path(file["file_name"]).stem)

    for file in extracted:
        if file.get('Fallback'):
            continue
        for dep in file["imports"]:
            module = _clean_import(dep)
            if not is_stdlib(module) and module not in pathstem and module not in imports:
                imports.append(module)
    
    deps.text = ",".join(imports)

    files = ET.SubElement(root,"files")

    for file in extracted:
        if file.get('Fallback'):
            continue
        f = ET.SubElement(files,"f",{"p":file["file_name"],"e":file["ext"]})

        if file["imports"]:
                imp = ET.SubElement(f,"imp")
                mod =[]
                for im in file["imports"]:
                    clean = _clean_import(im)
                    if clean and clean not in mod:
                        mod.append(im)
                imp.text = ",".join(mod)

        if file["functions"]:
            for func in file["functions"]:
                fn = ET.SubElement(f,"fn",{"n":func["name"],"p":func["params"]})
        
        if file["classes"]:
            for clas in file["classes"]:
                cls = ET.SubElement(f,"cls",{"n":clas})
                for func in file["classes"][clas]:
                    fn = ET.SubElement(cls,"fn",{"n":func["name"],"p":func["params"]})
        
        if file["struct"]:
            struct = ET.SubElement(f,"struct",{"n":file["struct"]})
        
        if file["enum"]:
            enum = ET.SubElement(f,"enum",{"n":file["enum"]})


    out = _out_path("structure.xml")
    tree = ET.ElementTree(root)
    ET.indent(tree)
    tree.write(str(out), encoding="utf-8", xml_declaration=True)
    return out.resolve()
        
    
def gen_summ(extracted, reponame):
    summariser = Summariser()
    root = ET.Element("repo", {"n": str(reponame)})
    meta = ET.SubElement(root, "meta")
    deps = ET.SubElement(meta, "dep")
    imports = []
    pathstem = []
    filenames = []

    for file in extracted:
        if file.get('Fallback'):
            continue
        filenames.append(Path(file["file_name"]))
        pathstem.append(Path(file["file_name"]).stem)

    for file in extracted:
        if file.get('Fallback'):
            continue
        for dep in file["imports"]:
            module = _clean_import(dep)
            if module and not is_stdlib(module) and module not in pathstem and module not in imports:
                imports.append(module)

    deps.text = ",".join(imports)
    s = summariser.summarise_repo(reponame, imports, files=filenames)
    root.set("s", s)

    # ── build batch input ─────────────────────────────────────────────────
    files_data = []
    valid_files = []

    for file in extracted:
        if file.get('Fallback'):
            continue
        files_data.append({
            "path":      file["file_name"],
            "lang":      file["ext"],
            "imports":   [c for im in file["imports"] if (c := _clean_import(im))],
            "classes":   file["classes"],
            "functions": file["functions"],
        })
        valid_files.append(file)

    # ── batched summarisation with live spinner ───────────────────────────
    BATCH_SIZE = 20
    all_summaries = []
    try:
        from . import cli
        with cli.summary_progress_context(len(files_data)) as advance:
            for i in range(0, len(files_data), BATCH_SIZE):
                chunk = files_data[i : i + BATCH_SIZE]
                batch_summaries = summariser.summarise_files_batch(chunk)
                all_summaries.extend(batch_summaries)
                advance(
                    len(chunk),
                    label=f"batch {i // BATCH_SIZE + 1} / {((len(files_data) - 1) // BATCH_SIZE) + 1}"
                )

    except ImportError:
        # no UI — run silently
        for i in range(0, len(files_data), BATCH_SIZE):
            chunk = files_data[i : i + BATCH_SIZE]
            all_summaries.extend(summariser.summarise_files_batch(chunk))

    # ── build XML ─────────────────────────────────────────────────────────
    files_el = ET.SubElement(root, "files")

    for file, fs in zip(valid_files, all_summaries):
        mod = []
        f = ET.SubElement(files_el, "f", {
            "p": file["file_name"],
            "e": file["ext"],
            "s": fs
        })

        if file["imports"]:
            imp = ET.SubElement(f, "imp")
            for im in file["imports"]:
                clean = _clean_import(im)
                if clean and clean not in mod:
                    mod.append(clean)
            imp.text = ",".join(mod)

        if file["functions"]:
            for func in file["functions"]:
                ET.SubElement(f, "fn", {
                    "n": func["name"],
                    "p": func["params"]
                })

        if file["classes"]:
            for clas in file["classes"]:
                cls = ET.SubElement(f, "cls", {"n": clas})
                for func in file["classes"][clas]:
                    ET.SubElement(cls, "fn", {
                        "n": func["name"],
                        "p": func["params"]
                    })

        if file["struct"]:
            ET.SubElement(f, "struct", {"n": ",".join(file["struct"])})

        if file["enum"]:
            ET.SubElement(f, "enum", {"n": ",".join(file["enum"])})

    out = _out_path("summary.xml")
    tree = ET.ElementTree(root)
    ET.indent(tree)
    tree.write(str(out), encoding="utf-8", xml_declaration=True)
    return out.resolve()


def gen_concat(valid,reponame):
    root = ET.Element("repo",{"n":str(reponame)})
    
    for file in valid:
        with open(Path(file["abspath"]).resolve(),"r",encoding="utf8") as f:
            content = f.read()
        fl = ET.SubElement(root,"file",{"n":file["relpath"]})
        src = ET.SubElement(fl,"src")
        indented = "\n".join("\t\t" + line for line in content.splitlines())
        indented = security.redact(indented)
        src.text = "\n" + indented + "\n\t"
    
    out = _out_path("concat.xml")
    tree = ET.ElementTree(root)
    ET.indent(tree)
    tree.write(str(out), encoding="utf-8", xml_declaration=True)
    return out.resolve()