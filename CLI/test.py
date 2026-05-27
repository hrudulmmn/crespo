import config
from pathlib import Path
from tree_sitter import QueryCursor,Parser

def get_parent(node):
    CLASS_NODE_TYPES = {
        "class_definition",
        "class_declaration",
        "impl_item",
    }

    ROOT_NODE_TYPES = {
        "module",
        "program",
        "source_file",
        "translation_unit",
    }

    current = node.parent

    while current is not None:
        if current.type in CLASS_NODE_TYPES:
            name_node = current.child_by_field_name("name")
            if name_node:
                return name_node.text  # already string in 0.25.2

        if current.type in ROOT_NODE_TYPES:
            return None

        current = current.parent

    return None


def extract(file):
    ext = Path(file).suffix.lower()
    configs = config.get_config()
    lang_config = configs.get(ext)

    if not lang_config:
        return {"fallback": True}

    
    lang_obj = lang_config["lang_obj"]
    parser = Parser(lang_obj)
    query = lang_obj.query(lang_config["query"])

    with open(file, encoding="utf8", errors="ignore") as f:
        source = f.read()

    source_byte = source.encode("utf8",errors="ignore")
    # 0.25.2 takes string directly
    tree = parser.parse(source_byte)
    cursor = QueryCursor(query=query)
    # returns dict in 0.25.2
    captures = cursor.captures(tree.root_node)

    functions = []
    imports = []
    classes = {}
    struct = []
    enum = []

    # sort by position in source for correct pairing
    func_name_nodes = sorted(
        captures.get("func_name", []),
        key=lambda n: n.start_byte
    )
    func_param_nodes = sorted(
        captures.get("func_params", []),
        key=lambda n: n.start_byte
    )

    # pair by index
    for i, name_node in enumerate(func_name_nodes):
        name = name_node.text  # already string

        params = ""
        if i < len(func_param_nodes):
            params = func_param_nodes[i].text

        parent = get_parent(name_node)
        fn = {"name": name, "params": params}

        if parent:
            if parent not in classes:
                classes[parent] = []
            classes[parent].append(fn)
        else:
            functions.append(fn)

    # imports
    for capture_name in [
        "imp", "imp_from",
        "imp_symbol", "imp_source"
    ]:
        for node in captures.get(capture_name, []):
            text = node.text
            if text not in imports:
                imports.append(text)

    # classes
    for capture_name in [
        "class_name", "interface_name",
        "impl_for", "type_name", "jsx_component"
    ]:
        for node in captures.get(capture_name, []):
            text = node.text
            if text not in classes:
                classes[text] = []

    # structs
    for node in captures.get("struct_name", []):
        text = node.text
        if text not in struct:
            struct.append(text)

    # enums
    for node in captures.get("enum_name", []):
        text = node.text
        if text not in enum:
            enum.append(text)

    return {
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "struct": struct,
        "enum": enum
    }