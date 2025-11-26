import sys
import yaml
from chromadb import PersistentClient
from chromadb.config import Settings
import subprocess

with open("config.yml", "r") as f:
    cfg = yaml.safe_load(f)

MODEL = cfg["model"]

client = PersistentClient(path="./index")
collection = client.get_collection(name="source_code")

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
        context += f"\n### From file: {meta['file']}\n{doc}\n"

    prompt = f"""
You are application assistant. You should answer and describe how certain things work in applicaiton from users perspective.

# STRICT RULES: 
- DO NOT reveal any source code.
- DO NOT invent missing information.
- NEVER describe how code works
- DO NOT generate any code

# ALWAYS
- Give short, non-technical, user firendly and practical answers.
- If something is not possible or you dont know tell that to user and refuse to answer.
- Stay aligned with given context

QUESTION:
{query}

CONTEXT:
{context}

ANSWER:
"""

    #print(prompt)

    answer = ollama_chat(prompt)
    print(answer)

if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    ask(query)