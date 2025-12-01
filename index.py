import os
from chromadb import PersistentClient
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import tree_sitter_c_sharp as ts_csharp
import tree_sitter_javascript as ts_javascript
import tree_sitter_typescript as ts_typescript
import tree_sitter_php as ts_php
from tree_sitter import Language, Parser
from config_loader import load_config

cfg = load_config()

PROJECT_PATH = cfg["project_path"]
CHUNK_SIZE = cfg["chunk_size"]
OVERLAP = cfg["chunk_overlap"]
EMBED_MODEL = cfg["embed_model"]
EXCLUDED_DIRS = cfg["excluded_dirs"]

LANGUAGES = {
    ".cs": Language(ts_csharp.language()),
    ".js": Language(ts_javascript.language()),
    ".jsx": Language(ts_javascript.language()),
    ".ts": Language(ts_typescript.language_typescript()),
    ".tsx": Language(ts_typescript.language_tsx()),
    ".php": Language(ts_php.language_php()),
}

AST_CHUNK_TYPES = {
    ".cs": [
        "class_declaration",
        "struct_declaration",
        "interface_declaration",
        "enum_declaration",
        "method_declaration",
        "constructor_declaration",
        "property_declaration",
        "namespace_declaration",
    ],
    ".js": [
        "class_declaration",
        "function_declaration",
        "arrow_function",
        "method_definition",
        "variable_declaration",
        "export_statement",
    ],
    ".jsx": [
        "class_declaration",
        "function_declaration",
        "arrow_function",
        "method_definition",
        "variable_declaration",
        "export_statement",
    ],
    ".ts": [
        "class_declaration",
        "function_declaration",
        "arrow_function",
        "method_definition",
        "interface_declaration",
        "type_alias_declaration",
        "enum_declaration",
        "export_statement",
    ],
    ".tsx": [
        "class_declaration",
        "function_declaration",
        "arrow_function",
        "method_definition",
        "interface_declaration",
        "type_alias_declaration",
        "enum_declaration",
        "export_statement",
    ],
    ".php": [
        "class_declaration",
        "function_definition",
        "method_declaration",
        "interface_declaration",
        "trait_declaration",
    ],
}

client = PersistentClient(path="./index")
collection = client.get_or_create_collection(
    name="source_code",
    embedding_function=embedding_functions.OllamaEmbeddingFunction(
        model_name=EMBED_MODEL
    )
)


def get_node_name(node, source_bytes):
    name_node = node.child_by_field_name("name")
    if name_node:
        return source_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8")
    return None


def extract_ast_chunks(source_code: str, ext: str):
    if ext not in LANGUAGES:
        return None
    
    parser = Parser(LANGUAGES[ext])
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)
    
    chunk_types = AST_CHUNK_TYPES.get(ext, [])
    chunks = []
    
    def traverse(node, parent_context=""):
        node_type = node.type
        
        current_context = parent_context
        if node_type in ["class_declaration", "struct_declaration", "interface_declaration", "namespace_declaration"]:
            name = get_node_name(node, source_bytes)
            if name:
                current_context = f"{parent_context}.{name}" if parent_context else name
        
        if node_type in chunk_types:
            start = node.start_byte
            end = node.end_byte
            text = source_bytes[start:end].decode("utf-8")
            name = get_node_name(node, source_bytes)
            
            chunk_info = {
                "text": text,
                "type": node_type,
                "name": name,
                "context": current_context,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
            }
            chunks.append(chunk_info)
        
        for child in node.children:
            traverse(child, current_context)
    
    traverse(tree.root_node)
    return chunks


def chunk_text(text, size, overlap):
    chunks = []
    start = 0

    while start < len(text):
        end = start + size
        chunks.append({"text": text[start:end], "type": "text_chunk", "name": None, "context": "", "start_line": None, "end_line": None})
        start += size - overlap

    return chunks


def is_source_file(path):
    return any(path.endswith(ext) for ext in [
        ".cs", ".php", ".js", ".ts", ".jsx", ".tsx",
        ".json", ".yml", ".yaml", ".xml", ".sql", ".md", ".py"
    ])


def get_file_extension(filepath):
    return os.path.splitext(filepath)[1].lower()


def index_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    ext = get_file_extension(filepath)
    
    chunks = extract_ast_chunks(content, ext)
    
    if chunks is None or len(chunks) == 0:
        chunks = chunk_text(content, CHUNK_SIZE, OVERLAP)
        print(f"  [text chunking] {len(chunks)} chunks")
    else:
        print(f"  [AST chunking] {len(chunks)} chunks")

    for i, chunk in enumerate(chunks):
        if chunk["name"]:
            chunk_id = f"{filepath}::{chunk['type']}::{chunk['name']}_{i}"
        else:
            chunk_id = f"{filepath}_{i}"
        
        print(f"  ADDING: {chunk_id}")

        metadata = {
            "file": filepath,
            "type": chunk["type"],
        }
        if chunk["name"]:
            metadata["name"] = chunk["name"]
        if chunk["context"]:
            metadata["context"] = chunk["context"]
        if chunk["start_line"] is not None:
            metadata["start_line"] = chunk["start_line"]
        if chunk["end_line"] is not None:
            metadata["end_line"] = chunk["end_line"]

        collection.add(
            ids=[chunk_id],
            documents=[chunk["text"]],
            metadatas=[metadata]
        )


def index_project():   
    for root, dirs, files in os.walk(PROJECT_PATH):    
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        for file in files:
            full = os.path.join(root, file)
            if is_source_file(full):
                print(f"Indexing: {full}")
                index_file(full)

    print("Done.")


if __name__ == "__main__":
    index_project()