import tree_sitter_language_pack as lang_pack
import config
from pathlib import Path


def get_parent(node):
    CLASS_NODE_TYPES = {
        "class_definition",    # Python
        "class_declaration",   # JS, TS, Java
        "impl_item",           # Rust
    }
    
    ROOT_NODE_TYPES = {
        "module",              # Python
        "program",             # JS, TS
        "source_file",         # Rust, Go
        "translation_unit",    # C, C++
    }

    current = node.parent

    while current is not None:
        if current.type in CLASS_NODE_TYPES:
            name_node = current.child_by_field_name("name")
        
            if name_node:
                return name_node.text.decode("utf8",errors="ignore")
        
        if current.type in ROOT_NODE_TYPES:
            return None
        
        current=current.parent
        
    return None

def get_docstring(node):
    func_node = node.parent  
    body = func_node.child_by_field_name("body")
    if not body or not body.children:
        return None
    first = body.children[0]
    if first.type == "expression_statement" and first.children:
        inner = first.children[0]
        if inner.type == "string":
            return inner.text.decode("utf8", errors="ignore").strip('"\' \n')
    return None

def extract(file):
    ext = Path(file).suffix.lower()
    configs = config.get_config()
    lang_config = configs.get(ext)

    if not lang_config:
        return {"Fallback":True}
    
    parser = lang_config["parser"]
    lang_obj  =lang_config["lang_obj"]
    try:
        query = lang_obj.query(lang_config["query"])
    except Exception as e:
        print(f"Query failed for ext: {ext}")
        print(f"Query string:\n{lang_config['query']}")
        raise

    with open(file,encoding="utf8",errors="ignore") as f:
        source = f.read()
    
    tree = parser.parse(source)
    captures = query.query(tree.root_node)

    functions=[]
    imports=[]
    classes = {}
    struct=[]
    enum=[]

    last_func = None
    last_node = None

    for node,capture in captures:
        text = node.text.decode("utf8",errors="ignore")

        if capture=="func_name":
            last_func=text
            last_node=node

        elif capture=="func_params":
            if last_func:
                parent = get_parent(last_node)
                docstring = get_docstring(last_node)
                fn = {"name":last_func,"params":text,"docstring":docstring}

                if parent:
                    if parent not in classes:
                        classes[parent]=[]
                    classes[parent].append(fn)
                else:
                    functions.append(fn)  

                last_func=None
                last_node=None
        
        elif capture in ["imp","imp_from","imp_symbol","imp_source"]:
            if text not in imports:
                imports.append(text)
        
        elif capture in ["class_name","interface_name","impl_for","type_name","jsx_component"]:
            if text not in classes:
                classes[text]=[]
        
        elif capture=="struct_name":
            if text not in struct:
                struct.append(text)
            
        elif capture=="enum_name":
            if text not in enum:
                enum.append(text)
        
    return {"function":functions,"classes":classes,"imports":imports,"struct":struct,"enum":enum}
    
    



