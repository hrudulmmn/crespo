import tree_sitter_language_pack as lang_pack
import config
from pathlib import Path
from tree_sitter import QueryCursor,Parser
import security


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

def extract_body(func_node,source_bytes,ext)->str:
    if not func_node:
        return ""
    body_node = func_node.child_by_field_name("body")
    if not body_node:
        return source_bytes[func_node.start_byte:func_node.end_byte].decode("utf8",errors="ignore")
    
    body = source_bytes[body_node.start_byte:func_node.end_byte].decode("utf8",errors="ignore").strip()
    body = strip_body(body,ext)
    body = truncate_body(body)
    return body



def extract_struct(file,mode:str,rel_path=None):
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
        name = node_name.text.decode("utf8",errors="ignore")

        params = ""
        if i < len(param_nodes):
            params = param_nodes[i].text.decode("utf8",errors="ignore")

        
        parent = get_parent(node_name)
        body = extract_body(node_name.parent,source_bytes=source_bytes,ext=ext)
        if mode =="summarize":
            body = security.redact(body)
            fn = {"name":name,"params":params,"body":body}
        else:
            fn = {"name":name,"params":params}

        if parent:
            if parent not in classes:
                classes[parent]=[]
            classes[parent].append(fn)
        else:
            functions.append(fn)  

    for capture in ["imp","imp_from","imp_source"]:
        for  node in captures.get(capture,[]):
            text=node.text.decode("utf8",errors="ignore")
            if text not in imports:
                imports.append(text)
    
    for capture in ["class_name","interface_name","impl_for","type_name","jsx_component"]:
        for node in captures.get(capture,[]):
            text = node.text.decode("utf8",errors="ignore")
            if text not in classes:
                classes[text]=[]
    
    for node in captures.get("struct_name",[]):
        text = node.text.decode("utf8",errors="ignore")
        if text not in struct:
            struct.append(text)
        
    for node in captures.get("enum_name",[]):
        text=node.text.decode("utf8",errors="ignore")
        if text not in enum:
            enum.append(text)
        
    return {"file_name":rel_path or str(file),"ext":ext,"functions":functions,"classes":classes,"imports":imports,"struct":struct,"enum":enum}
    
    

def strip_body(body: str, extension: str) -> str:
    COMMENT_CONFIG = {
    ".py": {
        "single": ["#"],
        "block": []
    },
    ".js": {
        "single": ["//"],
        "block": [("/*", "*/")]
    },
    ".jsx": {
        "single": ["//"],
        "block": [("/*", "*/")]
    },
    ".ts": {
        "single": ["//"],
        "block": [("/*", "*/")]
    },
    ".tsx": {
        "single": ["//"],
        "block": [("/*", "*/")]
    },
    ".java": {
        "single": ["//"],
        "block": [("/*", "*/")]
    },
    ".go": {
        "single": ["//"],
        "block": [("/*", "*/")]
    },
    ".rs": {
        "single": ["//"],
        "block": [("/*", "*/")]
    },
    ".c": {
        "single": ["//"],
        "block": [("/*", "*/")]
    },
    ".h": {
        "single": ["//"],
        "block": [("/*", "*/")]
    },
    ".cpp": {
        "single": ["//"],
        "block": [("/*", "*/")]
    },
    ".hpp": {
        "single": ["//"],
        "block": [("/*", "*/")]
    },
}
    config = COMMENT_CONFIG.get(
        extension,
        {"single": ["#", "//"], "block": [("/*", "*/")]}
    )

    lines = body.splitlines()
    cleaned = []

    in_block = False
    block_end = None

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        # Currently inside block comment
        if in_block:
            if block_end in stripped:
                in_block = False
            continue

        # Single-line comments
        if any(stripped.startswith(marker) for marker in config["single"]):
            continue

        # Block comments
        started_block = False
        for start, end in config["block"]:
            if stripped.startswith(start):
                started_block = True

                # Multi-line block comment
                if end not in stripped[len(start):]:
                    in_block = True
                    block_end = end

                break

        if started_block:
            continue

        cleaned.append(line)

    return "\n".join(cleaned)

def truncate_body(body: str) -> str:
    lines = body.split("\n")
    
    if len(lines) <= 35:
        return body
    
    head = lines[:20]  # core logic
    tail = lines[-10:]  # return value
    
    return (
        "\n".join(head) +
        "\n# ...\n" +
        "\n".join(tail)
    )

