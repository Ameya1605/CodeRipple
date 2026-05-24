import os
import uuid
from typing import List

try:
    import tree_sitter_java
    from tree_sitter import Language, Parser
    JAVA_LANGUAGE = tree_sitter_java.language()
except ImportError:
    JAVA_LANGUAGE = None

from backend.indexer.schema import CodeChunk, ParameterSchema

def get_node_text(node, source_code: bytes) -> str:
    return source_code[node.start_byte:node.end_byte].decode('utf-8')

def parse_java_file(file_path: str, repo_id: str) -> List[CodeChunk]:
    if not os.path.exists(file_path) or JAVA_LANGUAGE is None:
        return []
    
    with open(file_path, "rb") as f:
        source_code = f.read()

    parser = Parser(JAVA_LANGUAGE)
    tree = parser.parse(source_code)
    root_node = tree.root_node

    chunks: List[CodeChunk] = []

    def traverse(node, current_class=None):
        if node.type in ['class_declaration', 'interface_declaration']:
            name_node = node.child_by_field_name('name')
            if name_node:
                name = get_node_text(name_node, source_code)
                symbol_type = "class" if node.type == 'class_declaration' else "interface"
                
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
                    language="java",
                    is_exported=True, # simplifying
                )
                chunks.append(chunk)
                current_class = f"{current_class}.{name}" if current_class else name

        elif node.type == 'method_declaration':
            name_node = node.child_by_field_name('name')
            if name_node:
                name = get_node_text(name_node, source_code)
                
                params = []
                params_node = node.child_by_field_name('parameters')
                if params_node:
                    for param_node in params_node.named_children:
                        if param_node.type == 'formal_parameter':
                            p_name = param_node.child_by_field_name('name')
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
                    signature=f"{name}()",
                    content=get_node_text(node, source_code),
                    language="java",
                    parameters=params,
                    is_exported=True # simplifying
                )
                chunks.append(chunk)

        for child in node.children:
            traverse(child, current_class)

    traverse(root_node)
    return chunks
