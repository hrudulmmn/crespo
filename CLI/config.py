import tree_sitter_language_pack as lang_pack

def get_config():
    LANGUAGE_CONFIGS = {

        # ── Python ──────────────────────────────────────────────────────────────
        ".py": {
            "parser": lang_pack.get_parser("python"),
            "lang_obj": lang_pack.get_language("python"),
            "query": """
                (import_statement name: (dotted_name) @imp)
                (import_from_statement
                    module_name: (dotted_name) @imp_from
                    name: (dotted_name) @imp_symbol)
                (class_definition
                    name: (identifier) @class_name)
                (function_definition
                    name: (identifier) @func_name
                    parameters: (parameters) @func_params)
            """
        },

        # ── JavaScript ──────────────────────────────────────────────────────────
        ".js": {
            "parser": lang_pack.get_parser("javascript"),
            "lang_obj": lang_pack.get_language("javascript"),
            "query": """
                (import_statement source: (string) @imp_source)
                (import_specifier name: (identifier) @imp_symbol)
                (class_declaration name: (identifier) @class_name)
                (function_declaration
                    name: (identifier) @func_name
                    parameters: (formal_parameters) @func_params)
                (method_definition
                    name: (property_identifier) @func_name
                    parameters: (formal_parameters) @func_params)
                (lexical_declaration
                    (variable_declarator
                        name: (identifier) @func_name
                        value: (arrow_function
                            parameters: (formal_parameters) @func_params)))
            """
        },

        # ── TypeScript ──────────────────────────────────────────────────────────
        ".ts": {
            "parser": lang_pack.get_parser("typescript"),
            "lang_obj": lang_pack.get_language("typescript"),
            "query": """
                (import_statement source: (string) @imp_source)
                (import_specifier name: (identifier) @imp_symbol)
                (class_declaration name: (type_identifier) @class_name)
                (interface_declaration name: (type_identifier) @interface_name)
                (function_declaration
                    name: (identifier) @func_name
                    parameters: (formal_parameters) @func_params)
                (method_definition
                    name: (property_identifier) @func_name
                    parameters: (formal_parameters) @func_params)
                (lexical_declaration
                    (variable_declarator
                        name: (identifier) @func_name
                        value: (arrow_function
                            parameters: (formal_parameters) @func_params)))
            """
        },

        # ── TSX ─────────────────────────────────────────────────────────────────
        ".tsx": {
            "parser": lang_pack.get_parser("tsx"),
            "lang_obj": lang_pack.get_language("tsx"),
            "query": """
                (import_statement source: (string) @imp_source)
                (import_specifier name: (identifier) @imp_symbol)
                (class_declaration name: (type_identifier) @class_name)
                (interface_declaration name: (type_identifier) @interface_name)
                (function_declaration
                    name: (identifier) @func_name
                    parameters: (formal_parameters) @func_params)
                (method_definition
                    name: (property_identifier) @func_name
                    parameters: (formal_parameters) @func_params)
                (jsx_element
                    open_tag: (jsx_opening_element
                        name: (identifier) @jsx_component))
                (lexical_declaration
                    (variable_declarator
                        name: (identifier) @func_name
                        value: (arrow_function
                            parameters: (formal_parameters) @func_params)))
            """
        },

        # ── Java ────────────────────────────────────────────────────────────────
        ".java": {
            "parser": lang_pack.get_parser("java"),
            "lang_obj": lang_pack.get_language("java"),
            "query": """
                (import_declaration (scoped_identifier) @imp)
                (class_declaration name: (identifier) @class_name)
                (interface_declaration name: (identifier) @interface_name)
                (method_declaration
                    name: (identifier) @func_name
                    parameters: (formal_parameters) @func_params)
            """
        },

        # ── Go ──────────────────────────────────────────────────────────────────
        ".go": {
            "parser": lang_pack.get_parser("go"),
            "lang_obj": lang_pack.get_language("go"),
            "query": """
                (import_declaration
                    (imp_spec path: (interpreted_string_literal) @imp))
                (type_declaration
                    (type_spec name: (type_identifier) @type_name))
                (function_declaration
                    name: (identifier) @func_name
                    parameters: (parameter_list) @func_params)
                (method_declaration
                    receiver: (parameter_list) @receiver
                    name: (field_identifier) @func_name
                    parameters: (parameter_list) @func_params)
            """
        },

        # ── Rust ────────────────────────────────────────────────────────────────
        ".rs": {
            "parser": lang_pack.get_parser("rust"),
            "lang_obj": lang_pack.get_language("rust"),
            "query": """
                (use_declaration argument: (scoped_identifier) @imp)
                (struct_item name: (type_identifier) @struct_name)
                (enum_item name: (type_identifier) @enum_name)
                (impl_item type: (type_identifier) @impl_for)
                (function_item
                    name: (identifier) @func_name
                    parameters: (parameters) @func_params)
            """
        },

        # ── C ───────────────────────────────────────────────────────────────────
        ".c": {
            "parser": lang_pack.get_parser("c"),
            "lang_obj": lang_pack.get_language("c"),
            "query": """
                (preproc_include path: (string_literal) @imp)
                (struct_specifier name: (type_identifier) @struct_name)
                (function_definition
                    declarator: (function_declarator
                        declarator: (identifier) @func_name
                        parameters: (parameter_list) @func_params))
            """
        },

        # ── C++ ─────────────────────────────────────────────────────────────────
        ".cpp": {
            "parser": lang_pack.get_parser("cpp"),
            "lang_obj": lang_pack.get_language("cpp"),
            "query": """
                (preproc_include path: (string_literal) @imp)
                (class_specifier name: (type_identifier) @class_name)
                (struct_specifier name: (type_identifier) @struct_name)
                (function_definition
                    declarator: (function_declarator
                        declarator: (identifier) @func_name
                        parameters: (parameter_list) @func_params))
            """
        },
    }

    LANGUAGE_CONFIGS[".jsx"] = LANGUAGE_CONFIGS[".js"]
    LANGUAGE_CONFIGS[".h"]   = LANGUAGE_CONFIGS[".c"]
    LANGUAGE_CONFIGS[".hpp"] = LANGUAGE_CONFIGS[".cpp"]

    return LANGUAGE_CONFIGS