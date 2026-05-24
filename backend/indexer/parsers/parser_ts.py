import os
import uuid
import tree_sitter_typescript
from tree_sitter import Language, Parser
from typing import List, Optional
from backend.indexer.schema import CodeChunk, ParameterSchema

TS_LANGUAGE = tree_sitter_typescript.language_typescript()

def get_node_text(node, source_code: bytes) -> str:
    return source_code[node.start_byte:node.end_byte].decode('utf-8')

def parse_ts_file(file_path: str, repo_id: str) -> List[CodeChunk]:
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, "rb") as f:
        source_code = f.read()

    parser = Parser(TS_LANGUAGE)
    tree = parser.parse(source_code)
    root_node = tree.root_node

    chunks: List[CodeChunk] = []

    def extract_calls(node) -> List[str]:
        calls = []
        def find_calls(n):
            if n.type == 'call_expression':
                func_node = n.child_by_field_name('function')
                if func_node:
                    if func_node.type == 'identifier':
                        calls.append(get_node_text(func_node, source_code))
                    elif func_node.type == 'member_expression':
                        # For obj.method(), we extract 'property'
                        method_node = func_node.child_by_field_name('property')
                        if method_node:
                            calls.append(get_node_text(method_node, source_code))
            for child in n.children:
                find_calls(child)
        find_calls(node)
        return list(set(calls))

    def traverse(node, current_class=None):
        if node.type in ['class_declaration', 'interface_declaration']:
            name_node = node.child_by_field_name('name')
            if name_node:
                name = get_node_text(name_node, source_code)
                symbol_type = "class" if node.type == 'class_declaration' else "interface"
                
                # Extract heritage (extends/implements)
                heritage = []
                for child in node.children:
                    if child.type in ['extends_clause', 'implements_clause']:
                        for type_node in child.children:
                            if type_node.type == 'type_list':
                                for t in type_node.children:
                                    if t.type == 'type_identifier':
                                        heritage.append(get_node_text(t, source_code))
                            elif type_node.type == 'type_identifier':
                                heritage.append(get_node_text(type_node, source_code))
                
                chunk = CodeChunk(
                    chunk_id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    file_path=file_path,
                    symbol_type=symbol_type,
                    symbol_name=name,
                    qualified_name=f"{current_class}.{name}" if current_class else name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    signature=f"{symbol_type} {name}",
                    content=get_node_text(node, source_code),
                    language="typescript",
                    is_exported=node.parent and node.parent.type == 'export_statement',
                    contract_data={
                        "qualified_name": f"{current_class}.{name}" if current_class else name,
                        "heritage": heritage,
                        "visibility": "public" # TS default
                    }
                )
                chunks.append(chunk)
                current_class = f"{current_class}.{name}" if current_class else name
                
        elif node.type in ['function_declaration', 'method_definition', 'arrow_function']:
            name = None
            if node.type == 'function_declaration' or node.type == 'method_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = get_node_text(name_node, source_code)
            elif node.type == 'arrow_function':
                if node.parent and node.parent.type == 'variable_declarator':
                    name_node = node.parent.child_by_field_name('name')
                    if name_node:
                        name = get_node_text(name_node, source_code)
            
            if name:
                is_async = False
                for child in node.children:
                    if child.type == 'async':
                        is_async = True
                        break

                params = []
                params_node = node.child_by_field_name('parameters')
                if params_node:
                    for param_node in params_node.named_children:
                        if param_node.type == 'required_parameter':
                            p_name = param_node.child_by_field_name('pattern')
                            p_type = param_node.child_by_field_name('type')
                            if p_name:
                                params.append(ParameterSchema(
                                    name=get_node_text(p_name, source_code),
                                    type=get_node_text(p_type, source_code) if p_type else None
                                ))
                
                chunk = CodeChunk(
                    chunk_id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    file_path=file_path,
                    symbol_type="method" if current_class else "function",
                    symbol_name=name,
                    qualified_name=f"{current_class}.{name}" if current_class else name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    signature=f"function {name}()",
                    content=get_node_text(node, source_code),
                    language="typescript",
                    parameters=params,
                    calls=extract_calls(node),
                    is_async=is_async,
                    is_exported=node.parent and node.parent.type == 'export_statement'
                )
                chunks.append(chunk)

        for child in node.children:
            traverse(child, current_class)

    traverse(root_node)
    return chunks
