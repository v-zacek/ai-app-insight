import sys
import os
import yaml
from chromadb import PersistentClient
from chromadb.config import Settings
import subprocess

with open("config.yml", "r") as f:
    cfg = yaml.safe_load(f)

MODEL = cfg["model"]

client = PersistentClient(path="./index")
collection = client.get_collection(name="source_code")

def load_prompt_template():
    custom_template = "prompt_template.custom.md"
    default_template = "prompt_template.md"
    
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
    results = collection.query(
        query_texts=[query],
        n_results=8
    )

    context = ""
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        context += f"\n### From file: {meta['file']}\n```\n{doc}\n```\n"

    prompt = PROMPT_TEMPLATE.format(query=query, context=context)

    with open("prompt.log.md", "w", encoding="utf-8") as f:
        f.write(prompt)

    answer = ollama_chat(prompt)
    
    with open("prompt.log.md", "a", encoding="utf-8") as f:
        f.write("\n\n---\n\n# ANSWER\n\n")
        f.write(answer)
    
    print(answer)

if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    ask(query)