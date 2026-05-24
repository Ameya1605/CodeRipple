import os
import uuid
import tree_sitter_python
from tree_sitter import Language, Parser
from typing import List, Optional
from backend.indexer.schema import CodeChunk, ParameterSchema

PY_LANGUAGE = tree_sitter_python.language()

def get_node_text(node, source_code: bytes) -> str:
    return source_code[node.start_byte:node.end_byte].decode('utf-8')

def parse_python_file(file_path: str, repo_id: str) -> List[CodeChunk]:
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, "rb") as f:
        source_code = f.read()

    parser = Parser(PY_LANGUAGE)
    tree = parser.parse(source_code)
    root_node = tree.root_node

    chunks: List[CodeChunk] = []

    def extract_implicit_deps(node) -> List[str]:
        deps = []
        def find_implicit(n):
            # 1. String literals (potential topic/env names)
            if n.type == 'string':
                text = get_node_text(n, source_code).strip('"""\'\'\'')
                if len(text) > 3: # Ignore short strings
                    deps.append(f"string:{text}")
            
            # 2. Env var usage: os.environ.get("VAR") or os.getenv("VAR")
            if n.type == 'call':
                func_text = get_node_text(n.child_by_field_name('function'), source_code)
                if "getenv" in func_text or "environ.get" in func_text:
                    args = n.child_by_field_name('arguments')
                    if args and args.named_child_count > 0:
                        var_name = get_node_text(args.named_children[0], source_code).strip('"""\'\'\'')
                        deps.append(f"env:{var_name}")
            
            for child in n.children:
                find_implicit(child)
        find_implicit(node)
        return list(set(deps))

    def extract_calls(node) -> List[str]:
        calls = []
        def find_calls(n):
            if n.type == 'call':
                func_node = n.child_by_field_name('function')
                if func_node:
                    if func_node.type == 'identifier':
                        calls.append(get_node_text(func_node, source_code))
                    elif func_node.type == 'attribute':
                        # For obj.method(), we extract 'method'
                        method_node = func_node.child_by_field_name('attribute')
                        if method_node:
                            calls.append(get_node_text(method_node, source_code))
            for child in n.children:
                find_calls(child)
        find_calls(node)
        return list(set(calls))

    def traverse(node, current_class=None):
        if node.type == 'class_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                name = get_node_text(name_node, source_code)
                # Parse docstring
                docstring = None
                body_node = node.child_by_field_name('body')
                if body_node and body_node.named_child_count > 0:
                    first_stmt = body_node.named_children[0]
                    if first_stmt.type == 'expression_statement':
                        expr = first_stmt.named_children[0]
                        if expr.type == 'string':
                            docstring = get_node_text(expr, source_code).strip('"""\'\'\'')
                
                chunk = CodeChunk(
                    chunk_id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    file_path=file_path,
                    symbol_type="class",
                    symbol_name=name,
                    qualified_name=f"{current_class}.{name}" if current_class else name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    signature=f"class {name}:",
                    docstring=docstring,
                    content=get_node_text(node, source_code),
                    language="python",
                    is_exported=not name.startswith('_'),
                    parameters=[]
                )
                chunks.append(chunk)
                current_class = f"{current_class}.{name}" if current_class else name
        
        elif node.type == 'function_definition' or node.type == 'async_function_definition':
            is_async = node.type == 'async_function_definition'
            
            if node.type == 'async_function_definition':
                name_node = None
                for child in node.children:
                    if child.type == 'identifier':
                        name_node = child
                        break
            else:
                name_node = node.child_by_field_name('name')

            if name_node:
                name = get_node_text(name_node, source_code)
                
                # Parse docstring
                docstring = None
                body_node = node.child_by_field_name('body')
                if body_node and body_node.named_child_count > 0:
                    first_stmt = body_node.named_children[0]
                    if first_stmt.type == 'expression_statement':
                        expr = first_stmt.named_children[0]
                        if expr.type == 'string':
                            docstring = get_node_text(expr, source_code).strip('"""\'\'\'')

                # Parameters
                params = []
                params_node = node.child_by_field_name('parameters')
                signature = f"def {name}()"
                if params_node:
                    signature = f"def {name}{get_node_text(params_node, source_code)}"
                    for param_node in params_node.named_children:
                        if param_node.type == 'identifier':
                            params.append(ParameterSchema(name=get_node_text(param_node, source_code)))
                        elif param_node.type == 'typed_parameter':
                            p_name = param_node.child(0)
                            p_type = param_node.child(2)
                            if p_name and p_type:
                                params.append(ParameterSchema(
                                    name=get_node_text(p_name, source_code),
                                    type=get_node_text(p_type, source_code)
                                ))
                        elif param_node.type == 'default_parameter':
                            p_name = param_node.child(0)
                            if p_name:
                                params.append(ParameterSchema(
                                    name=get_node_text(p_name, source_code),
                                    required=False
                                ))

                # Return type
                return_type = None
                return_type_node = node.child_by_field_name('return_type')
                if return_type_node:
                    return_type = get_node_text(return_type_node, source_code)

                # Extract decorators
                decorators = []
                if node.parent and node.parent.type == 'decorated_definition':
                    for child in node.parent.children:
                        if child.type == 'decorator':
                            decorators.append(get_node_text(child, source_code).strip('@'))
                
                is_on_critical_path = any(d in ["app.route", "celery.task", "pytest.fixture"] for d in decorators)

                chunk = CodeChunk(
                    chunk_id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    file_path=file_path,
                    symbol_type="method" if current_class else "function",
                    symbol_name=name,
                    qualified_name=f"{current_class}.{name}" if current_class else name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    signature=signature,
                    docstring=docstring,
                    content=get_node_text(node, source_code),
                    language="python",
                    parameters=params,
                    return_type=return_type,
                    calls=extract_calls(node),
                    is_async=is_async,
                    is_exported=not name.startswith('_'),
                    is_on_critical_path=is_on_critical_path,
                    contract_data={
                        "qualified_name": f"{current_class}.{name}" if current_class else name,
                        "parameters": [p.model_dump() for p in params],
                        "return_type": return_type,
                        "is_async": is_async,
                        "visibility": "public" if not name.startswith('_') else "private",
                        "implicit_deps": extract_implicit_deps(node)
                    }
                )
                chunks.append(chunk)

        for child in node.children:
            traverse(child, current_class)

    traverse(root_node)
    return chunks
