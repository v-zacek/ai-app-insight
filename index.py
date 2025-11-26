import os
import yaml
from chromadb import PersistentClient
from chromadb.config import Settings
from chromadb.utils import embedding_functions

with open("config.yml", "r") as f:
    cfg = yaml.safe_load(f)

PROJECT_PATH = cfg["project_path"]
CHUNK_SIZE = cfg["chunk_size"]
OVERLAP = cfg["chunk_overlap"]
EMBED_MODEL = cfg["embed_model"]
EXCLUDED_DIRS = cfg["excluded_dirs"]

client = PersistentClient(path="./index")
collection = client.get_or_create_collection(
    name="source_code",
    embedding_function=embedding_functions.OllamaEmbeddingFunction(
        model_name=EMBED_MODEL
    )
)

def chunk_text(text, size, overlap):
    chunks = []
    start = 0

    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap

    return chunks

def is_source_file(path):
    return any(path.endswith(ext) for ext in [
        ".cs", ".php", ".js", ".ts", ".jsx", ".tsx",
        ".json", ".yml", ".yaml", ".xml", ".sql", ".md"
    ])

def index_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    chunks = chunk_text(content, CHUNK_SIZE, OVERLAP)

    for i, chunk in enumerate(chunks):
        chunk_id = f"{filepath}_{i}"
        print(f"ADDING: {chunk_id}")

        collection.add(
            ids=[chunk_id],
            documents=[chunk],
            metadatas=[{"file": filepath}]
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