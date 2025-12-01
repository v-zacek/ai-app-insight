import sys
import os
from chromadb import PersistentClient
from chromadb.config import Settings
import subprocess
from config_loader import load_config
from reranker import rerank_chunks

cfg = load_config()

MODEL = cfg["model"]
RERANK_CANDIDATES = cfg["rerank_candidates"]
RERANK_SELECT = cfg["rerank_select"]

client = PersistentClient(path="./index")
collection = client.get_collection(name="source_code")

def load_prompt_template():
    custom_template = os.path.join("prompt", "prompt_template.custom.md")
    default_template = os.path.join("prompt", "prompt_template.md")
    
    template_file = custom_template if os.path.exists(custom_template) else default_template
    
    with open(template_file, "r", encoding="utf-8") as f:
        return f.read()
    
PROMPT_TEMPLATE = load_prompt_template()

def ollama_chat(prompt):
    result = subprocess.run(
        ["ollama", "run", MODEL],
        input=prompt.encode(),
        stdout=subprocess.PIPE
    )
    return result.stdout.decode()

def ask(query):
    print("Collecting chunks ...")
    results = collection.query(
        query_texts=[query],
        n_results=RERANK_CANDIDATES
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    
    print("Reranking chunks ...")
    if len(documents) > 0:
        documents, metadatas = rerank_chunks(query, documents, metadatas, MODEL, RERANK_SELECT)
    
    context = ""
    for doc, meta in zip(documents, metadatas):
        context += f"\n### From file: {meta['file']}\n```\n{doc}\n```\n"

    prompt = PROMPT_TEMPLATE.format(query=query, context=context)

    os.makedirs("log", exist_ok=True)
    log_file = os.path.join("log", "prompt.log.md")

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(prompt)

    answer = ollama_chat(prompt)
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("\n\n---\n\n# ANSWER\n\n")
        f.write(answer)
    
    print(answer)

if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    ask(query)