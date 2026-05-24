import os
import uuid
import tree_sitter_go
from tree_sitter import Language, Parser
from typing import List
from backend.indexer.schema import CodeChunk, ParameterSchema

GO_LANGUAGE = tree_sitter_go.language()

def get_node_text(node, source_code: bytes) -> str:
    return source_code[node.start_byte:node.end_byte].decode('utf-8')

def parse_go_file(file_path: str, repo_id: str) -> List[CodeChunk]:
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, "rb") as f:
        source_code = f.read()

    parser = Parser(GO_LANGUAGE)
    tree = parser.parse(source_code)
    root_node = tree.root_node

    chunks: List[CodeChunk] = []

    def traverse(node, current_class=None):
        if node.type == 'type_declaration':
            for type_spec in node.named_children:
                if type_spec.type == 'type_spec':
                    name_node = type_spec.child_by_field_name('name')
                    type_node = type_spec.child_by_field_name('type')
                    if name_node and type_node and type_node.type in ['struct_type', 'interface_type']:
                        name = get_node_text(name_node, source_code)
                        symbol_type = "struct" if type_node.type == 'struct_type' else "interface"
                        
                        chunk = CodeChunk(
                            chunk_id=str(uuid.uuid4()),
                            repo_id=repo_id,
                            file_path=file_path,
                            symbol_type=symbol_type,
                            symbol_name=name,
                            qualified_name=name,
                            start_line=type_spec.start_point[0] + 1,
                            end_line=type_spec.end_point[0] + 1,
                            signature=f"type {name} {symbol_type}",
                            content=get_node_text(type_spec, source_code),
                            language="go",
                            is_exported=name[0].isupper() if name else False,
                        )
                        chunks.append(chunk)

        elif node.type in ['function_declaration', 'method_declaration']:
            name_node = node.child_by_field_name('name')
            if name_node:
                name = get_node_text(name_node, source_code)
                receiver = None
                if node.type == 'method_declaration':
                    receiver_node = node.child_by_field_name('receiver')
                    if receiver_node:
                        # Extract receiver type for qualified name
                        for child in receiver_node.named_children:
                            if child.type == 'parameter_declaration':
                                type_n = child.child_by_field_name('type')
                                if type_n:
                                    # handle pointer types
                                    if type_n.type == 'pointer_type':
                                        type_n = type_n.named_children[0]
                                    receiver = get_node_text(type_n, source_code)

                params = []
                params_node = node.child_by_field_name('parameters')
                if params_node:
                    for param_decl in params_node.named_children:
                        if param_decl.type == 'parameter_declaration':
                            p_type = param_decl.child_by_field_name('type')
                            for p_name_node in param_decl.named_children:
                                if p_name_node != p_type:
                                    params.append(ParameterSchema(
                                        name=get_node_text(p_name_node, source_code),
                                        type=get_node_text(p_type, source_code) if p_type else None
                                    ))
                
                chunk = CodeChunk(
                    chunk_id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    file_path=file_path,
                    symbol_type="method" if node.type == 'method_declaration' else "function",
                    symbol_name=name,
                    qualified_name=f"{receiver}.{name}" if receiver else name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    signature=f"func {name}()",
                    content=get_node_text(node, source_code),
                    language="go",
                    parameters=params,
                    is_exported=name[0].isupper() if name else False,
                )
                chunks.append(chunk)

        for child in node.children:
            traverse(child)

    traverse(root_node)
    return chunks
