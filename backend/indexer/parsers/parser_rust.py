import os
import uuid
import tree_sitter_rust
from tree_sitter import Language, Parser
from typing import List
from backend.indexer.schema import CodeChunk, ParameterSchema

RUST_LANGUAGE = tree_sitter_rust.language()

def get_node_text(node, source_code: bytes) -> str:
    return source_code[node.start_byte:node.end_byte].decode('utf-8')

def parse_rust_file(file_path: str, repo_id: str) -> List[CodeChunk]:
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, "rb") as f:
        source_code = f.read()

    parser = Parser(RUST_LANGUAGE)
    tree = parser.parse(source_code)
    root_node = tree.root_node

    chunks: List[CodeChunk] = []

    def traverse(node, current_impl=None):
        if node.type == 'impl_item':
            type_node = node.child_by_field_name('type')
            if type_node:
                current_impl = get_node_text(type_node, source_code)
                
        elif node.type in ['struct_item', 'trait_item']:
            name_node = node.child_by_field_name('name')
            if name_node:
                name = get_node_text(name_node, source_code)
                symbol_type = "struct" if node.type == 'struct_item' else "trait"
                
                chunk = CodeChunk(
                    chunk_id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    file_path=file_path,
                    symbol_type=symbol_type,
                    symbol_name=name,
                    qualified_name=name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    signature=f"{symbol_type} {name}",
                    content=get_node_text(node, source_code),
                    language="rust",
                    is_exported=node.parent and node.parent.type == 'visibility_modifier',
                )
                chunks.append(chunk)

        elif node.type == 'function_item':
            name_node = node.child_by_field_name('name')
            if name_node:
                name = get_node_text(name_node, source_code)
                
                params = []
                params_node = node.child_by_field_name('parameters')
                if params_node:
                    for param_node in params_node.named_children:
                        if param_node.type == 'parameter':
                            p_name = param_node.child_by_field_name('pattern')
                            p_type = param_node.child_by_field_name('type')
                            if p_name:
                                params.append(ParameterSchema(
                                    name=get_node_text(p_name, source_code),
                                    type=get_node_text(p_type, source_code) if p_type else None
                                ))
                
                is_async = False
                for child in node.children:
                    if child.type == 'async':
                        is_async = True
                        break

                chunk = CodeChunk(
                    chunk_id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    file_path=file_path,
                    symbol_type="method" if current_impl else "function",
                    symbol_name=name,
                    qualified_name=f"{current_impl}.{name}" if current_impl else name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    signature=f"fn {name}()",
                    content=get_node_text(node, source_code),
                    language="rust",
                    parameters=params,
                    is_async=is_async,
                    is_exported=node.parent and node.parent.type == 'visibility_modifier'
                )
                chunks.append(chunk)

        for child in node.children:
            if node.type != 'impl_item' or child.type != 'declaration_list':
                 traverse(child, current_impl)
            elif node.type == 'impl_item' and child.type == 'declaration_list':
                 traverse(child, current_impl)

    traverse(root_node)
    return chunks
