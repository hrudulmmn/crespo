import xml.etree.ElementTree as ET
import sys
from pathlib import Path
from summary import Summariser

def is_stdlib(module):
    
    return module in sys.stdlib_module_names


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
            module = dep.split(".")[0]
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
                imp.text = ",".join(file["imports"])

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


    tree = ET.ElementTree(root)
    ET.indent(tree)
    tree.write("output.xml", encoding="utf-8", xml_declaration=True)
        
    
def gen_summ(extracted,reponame):
    summariser = Summariser()
    root = ET.Element("repo",{"n":str(reponame)})
    meta = ET.SubElement(root,"meta")
    deps = ET.SubElement(meta,"dep")
    imports=[]
    pathstem=[]
    filenames=[]
    method=[]


    for file in extracted:
        if file.get('Fallback'):
            continue
        filenames.append(Path(file["file_name"]))
        pathstem.append(Path(file["file_name"]).stem)

    for file in extracted:
        if file.get('Fallback'):
            continue
        for dep in file["imports"]:
            module = dep.split(".")[0]
            if not is_stdlib(module) and module not in pathstem and module not in imports:
                imports.append(module)
    
    deps.text = ",".join(imports)
    s = summariser.summarise_repo(reponame,imports,files=filenames)
    root.set("s",s)

    files = ET.SubElement(root,"files")

    for file in extracted:
        if file.get('Fallback'):
            continue
        fs = summariser.summarise_file(file["file_name"],file["ext"],file["imports"],file["classes"],file["functions"])
        f = ET.SubElement(files,"f",{"p":file["file_name"],"e":file["ext"],"s":fs})

        if file["imports"]:
                imp = ET.SubElement(f,"imp")
                imp.text = ",".join(file["imports"])

        if file["functions"]:
            for func in file["functions"]:
                fns = summariser.summarise_fun(file["ext"],{"n":func["name"],"p":func["params"]},func["body"])
                fn = ET.SubElement(f,"fn",{"n":func["name"],"p":func["params"]})
        
        if file["classes"]:
            for clas in file["classes"]:
                cls = ET.SubElement(f,"cls",{"n":clas})
                for func in file["classes"][clas]:
                    fn = ET.SubElement(cls,"fn",{"n":func["name"],"p":func["params"]})
                    method.append({"n":func["name"],"p":func["params"]})
                cs = summariser.summarise_class(clas,file["ext"],method_signature=method)
                cls.set("s",cs)
        
        if file["struct"]:
            struct = ET.SubElement(f,"struct",{"n":file["struct"]})
        
        if file["enum"]:
            enum = ET.SubElement(f,"enum",{"n":file["enum"]})


    tree = ET.ElementTree(root)
    ET.indent(tree)
    tree.write("summarised.xml", encoding="utf-8", xml_declaration=True)