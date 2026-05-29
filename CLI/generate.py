import xml.etree.ElementTree as ET
import sys
from pathlib import Path

def is_stdlib(module):
    
    return module in sys.stdlib_module_names


def gen_struct(extracted,reponame):
    root = ET.Element("repo",{"n":str(reponame)})
    meta = ET.SubElement(root,"meta")
    deps = ET.SubElement(meta,"dep")
    imports=[]
    pathstem=[]

    for file in extracted:
        pathstem.append(Path(file["file_name"]).stem)

    for file in extracted:
        for dep in file["imports"]:
            module = dep.split(".")[0]
            if not is_stdlib(module) and module not in pathstem and module not in imports:
                imports.append(module)
    
    deps.text = ",".join(imports)

    files = ET.SubElement(root,"files")

    for file in extracted:
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
        
    