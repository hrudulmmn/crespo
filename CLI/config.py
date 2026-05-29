import tree_sitter_language_pack as lang_pack

# ─────────────────────────────────────────────────────────────────────────────
# All queries verified against official tree-sitter grammar node-types.json
# sources on GitHub. Rules applied:
#
# 1. Only use field: labels that actually exist in the grammar for that node.
#    e.g. import_from_statement has fields "module_name" and "name" (for
#    dotted_name/aliased_import children) but wildcard_import is an unnamed
#    CHILD, not a named field — so it must be matched without a field label.
#
# 2. Nested field constraints are valid (tree-sitter supports them) but the
#    field name must exist on the INNER node type too. When uncertain, drop
#    the field label and match by node type only — tree-sitter still finds it.
#
# 3. No (#eq?) predicates — not supported in all tree-sitter-python versions.
#
# 4. (import) is a valid primary_expression node in JS/TS for dynamic import.
# ─────────────────────────────────────────────────────────────────────────────

def get_config():
    LANGUAGE_CONFIGS = {

        # ── Python ──────────────────────────────────────────────────────────────
        # Grammar: github.com/tree-sitter/tree-sitter-python
        #
        # import_statement        fields: name → dotted_name | aliased_import
        # import_from_statement   fields: module_name → dotted_name | relative_import
        #                                 name → dotted_name | aliased_import
        #                         child (unnamed field): wildcard_import
        # aliased_import          fields: name → dotted_name
        #                                 alias → identifier
        # function_definition     fields: name, parameters, body, return_type
        # class_definition        fields: name, superclasses, body
        ".py": {
            "parser": lang_pack.get_parser("python"),
            "lang_obj": lang_pack.get_language("python"),
            "query": """
                (import_statement
                    name: (dotted_name) @imp)

                (aliased_import
                    name: (dotted_name) @imp
                    alias: (identifier) @imp_alias)

                (import_from_statement
                    module_name: (dotted_name) @imp_from
                    name: (dotted_name) @imp_symbol)

                (import_from_statement
                    module_name: (dotted_name) @imp_from
                    (wildcard_import) @imp_wildcard)

                (class_definition
                    name: (identifier) @class_name)

                (function_definition
                    name: (identifier) @func_name
                    parameters: (parameters) @func_params)
            """
        },

        # ── JavaScript ──────────────────────────────────────────────────────────
        # Grammar: github.com/tree-sitter/tree-sitter-javascript
        #
        # import_statement        fields: source → string
        #                         child: import_clause
        # import_clause           child: identifier (default), namespace_import,
        #                                named_imports
        # namespace_import        child: identifier
        # named_imports           child: import_specifier
        # import_specifier        fields: name → identifier
        #                                 alias → identifier  (for "a as b")
        # call_expression         fields: function → expression, arguments → arguments
        # (import) is a named node (primary_expression subtype) for dynamic import()
        ".js": {
            "parser": lang_pack.get_parser("javascript"),
            "lang_obj": lang_pack.get_language("javascript"),
            "query": """
                (import_statement
                    source: (string) @imp_source)

                (import_clause
                    (identifier) @imp_default)

                (namespace_import
                    (identifier) @imp_namespace)

                (import_specifier
                    name: (identifier) @imp_symbol)

                (import_specifier
                    name: (identifier) @imp_symbol
                    alias: (identifier) @imp_alias)

                (call_expression
                    function: (identifier) @_callee
                    arguments: (arguments (string) @imp_require))

                (call_expression
                    function: (import)
                    arguments: (arguments (string) @imp_dynamic))

                (class_declaration
                    name: (identifier) @class_name)

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
        # Grammar: github.com/tree-sitter/tree-sitter-typescript
        # Same import structure as JS. `import type { Foo }` uses the same
        # import_specifier node — the "type" keyword is an unnamed child.
        # class/interface use type_identifier instead of identifier for names.
        ".ts": {
            "parser": lang_pack.get_parser("typescript"),
            "lang_obj": lang_pack.get_language("typescript"),
            "query": """
                (import_statement
                    source: (string) @imp_source)

                (import_clause
                    (identifier) @imp_default)

                (namespace_import
                    (identifier) @imp_namespace)

                (import_specifier
                    name: (identifier) @imp_symbol)

                (import_specifier
                    name: (identifier) @imp_symbol
                    alias: (identifier) @imp_alias)

                (call_expression
                    function: (identifier) @_callee
                    arguments: (arguments (string) @imp_require))

                (call_expression
                    function: (import)
                    arguments: (arguments (string) @imp_dynamic))

                (class_declaration
                    name: (type_identifier) @class_name)

                (interface_declaration
                    name: (type_identifier) @interface_name)

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
        # Same as TS with jsx_element added.
        # jsx_element → open_tag field → jsx_opening_element
        # jsx_opening_element → name field → identifier | member_expression
        ".tsx": {
            "parser": lang_pack.get_parser("tsx"),
            "lang_obj": lang_pack.get_language("tsx"),
            "query": """
                (import_statement
                    source: (string) @imp_source)

                (import_clause
                    (identifier) @imp_default)

                (namespace_import
                    (identifier) @imp_namespace)

                (import_specifier
                    name: (identifier) @imp_symbol)

                (import_specifier
                    name: (identifier) @imp_symbol
                    alias: (identifier) @imp_alias)

                (call_expression
                    function: (identifier) @_callee
                    arguments: (arguments (string) @imp_require))

                (call_expression
                    function: (import)
                    arguments: (arguments (string) @imp_dynamic))

                (class_declaration
                    name: (type_identifier) @class_name)

                (interface_declaration
                    name: (type_identifier) @interface_name)

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
        # Grammar: github.com/tree-sitter/tree-sitter-java
        #
        # import_declaration  children (no named fields): scoped_identifier,
        #                      asterisk; the "static" keyword is an anonymous
        #                      child — no named field for it.
        # class_declaration   fields: name → identifier
        # interface_declaration fields: name → identifier
        # method_declaration  fields: name → identifier, parameters → formal_parameters
        ".java": {
            "parser": lang_pack.get_parser("java"),
            "lang_obj": lang_pack.get_language("java"),
            "query": """
                (import_declaration
                    (scoped_identifier) @imp)

                (import_declaration
                    (asterisk) @imp_wildcard)

                (class_declaration
                    name: (identifier) @class_name)

                (interface_declaration
                    name: (identifier) @interface_name)

                (method_declaration
                    name: (identifier) @func_name
                    parameters: (formal_parameters) @func_params)
            """
        },

        # ── Go ──────────────────────────────────────────────────────────────────
        # Grammar: github.com/tree-sitter/tree-sitter-go
        #
        # import_spec   fields: name → identifier (optional alias, ".", or "_")
        #                        path → interpreted_string_literal
        # type_spec     fields: name → type_identifier
        # function_declaration  fields: name → identifier, parameters → parameter_list
        # method_declaration    fields: receiver → parameter_list,
        #                                name → field_identifier,
        #                                parameters → parameter_list
        ".go": {
            "parser": lang_pack.get_parser("go"),
            "lang_obj": lang_pack.get_language("go"),
            "query": """
                (import_spec
                    path: (interpreted_string_literal) @imp)

                (import_spec
                    name: (identifier) @imp_alias
                    path: (interpreted_string_literal) @imp)

                (type_declaration
                    (type_spec
                        name: (type_identifier) @type_name))

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
        # Grammar: github.com/tree-sitter/tree-sitter-rust
        #
        # use_declaration   field: argument → scoped_identifier | scoped_use_list
        #                          | use_wildcard | use_as_clause | identifier
        # use_as_clause     fields: path → scoped_identifier | identifier
        #                           alias → identifier
        # use_list          unnamed children: identifier, use_as_clause, etc.
        # struct_item       fields: name → type_identifier
        # enum_item         fields: name → type_identifier
        # impl_item         fields: type → type_identifier | ...
        # function_item     fields: name → identifier, parameters → parameters
        ".rs": {
            "parser": lang_pack.get_parser("rust"),
            "lang_obj": lang_pack.get_language("rust"),
            "query": """
                (use_declaration
                    argument: (scoped_identifier) @imp)

                (use_declaration
                    argument: (scoped_use_list) @imp_grouped)

                (use_declaration
                    argument: (use_wildcard) @imp_glob)

                (use_as_clause
                    path: (scoped_identifier) @imp
                    alias: (identifier) @imp_alias)

                (use_list
                    (identifier) @imp_symbol)

                (struct_item
                    name: (type_identifier) @struct_name)

                (enum_item
                    name: (type_identifier) @enum_name)

                (impl_item
                    type: (type_identifier) @impl_for)

                (function_item
                    name: (identifier) @func_name
                    parameters: (parameters) @func_params)
            """
        },

        # ── C ───────────────────────────────────────────────────────────────────
        # Grammar: github.com/tree-sitter/tree-sitter-c
        #
        # preproc_include  fields: path → string_literal | system_lib_string
        # struct_specifier fields: name → type_identifier
        # function_definition → declarator field → function_declarator
        # function_declarator fields: declarator → identifier | ...
        #                             parameters → parameter_list
        ".c": {
            "parser": lang_pack.get_parser("c"),
            "lang_obj": lang_pack.get_language("c"),
            "query": """
                (preproc_include
                    path: (string_literal) @imp)

                (preproc_include
                    path: (system_lib_string) @imp_system)

                (struct_specifier
                    name: (type_identifier) @struct_name)

                (function_definition
                    declarator: (function_declarator
                        declarator: (identifier) @func_name
                        parameters: (parameter_list) @func_params))
            """
        },

        # ── C++ ─────────────────────────────────────────────────────────────────
        # Grammar: github.com/tree-sitter/tree-sitter-cpp
        #
        # Same as C plus:
        # using_declaration  child (no named field): qualified_identifier
        # namespace_alias_definition  fields: name → namespace_identifier
        #                             child (no named field): namespace_identifier
        # class_specifier    fields: name → type_identifier
        ".cpp": {
            "parser": lang_pack.get_parser("cpp"),
            "lang_obj": lang_pack.get_language("cpp"),
            "query": """
                (preproc_include
                    path: (string_literal) @imp)

                (preproc_include
                    path: (system_lib_string) @imp_system)

                (using_declaration
                    (qualified_identifier) @imp_using)

                (namespace_alias_definition
                    name: (namespace_identifier) @imp_alias
                    (namespace_identifier) @imp)

                (class_specifier
                    name: (type_identifier) @class_name)

                (struct_specifier
                    name: (type_identifier) @struct_name)

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