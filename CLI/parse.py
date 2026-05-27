import tree_sitter_language_pack as lang_pack
import config
from pathlib import Path
from tree_sitter import QueryCursor,Parser


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


def extract(file):
    ext = Path(file).suffix.lower()
    configs = config.get_config()
    lang_config = configs.get(ext)

    if not lang_config:
        return {"Fallback":True}
    
    
    lang_obj  =lang_config["lang_obj"]
    parser = Parser(lang_obj)
    query = lang_obj.query(lang_config["query"])
    

    with open(file,encoding="utf8",errors="ignore") as f:
        source = f.read()
    
    source_bytes = source.encode(encoding="utf8",errors="ignore")
    tree = parser.parse(source_bytes)
    cursor = QueryCursor(query)
    captures = cursor.captures(tree.root_node)

    functions=[]
    imports=[]
    classes = {}
    struct=[]
    enum=[]

    func_nodes = sorted(
        captures.get("func_name",[]),key=lambda n:n.start_byte
    )

    param_nodes = sorted(
        captures.get("func_params",[]),key=lambda n:n.start_byte
    )

    for i,node_name in enumerate(func_nodes):
        name = node_name.text

        params = ""
        if i < len(param_nodes):
            params = param_nodes[i].text

        
        parent = get_parent(node_name)
        fn = {"name":name,"params":params}

        if parent:
            if parent not in classes:
                classes[parent]=[]
            classes[parent].append(fn)
        else:
            functions.append(fn)  

        for capture in ["imp","imp_from","imp_symbol","imp_source"]:
            for  node in captures.get(capture,[]):
                text=node.text
                if text not in imports:
                    imports.append(text)
        
        for capture in ["class_name","interface_name","impl_for","type_name","jsx_component"]:
            for node in captures.get(capture,[]):
                text = node.text
                if text not in classes:
                    classes[text]=[]
        
        for node in captures.get("struct_name",[]):
            text = node.text
            if text not in struct:
                struct.append(text)
            
        for node in captures.get("enum_name",[]):
            text=node.text
            if text not in enum:
                enum.append(text)
        
    return {"function":functions,"classes":classes,"imports":imports,"struct":struct,"enum":enum}
    
    



