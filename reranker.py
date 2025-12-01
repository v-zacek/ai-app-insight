import subprocess
import os


def load_reranking_template():
    template_path = os.path.join("prompt", "reranking_prompt_template.md")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


RERANKING_TEMPLATE = load_reranking_template()
FIRST_RERANK = True


def rerank_chunks(query, documents, metadatas, model, chunks_to_select):
    global FIRST_RERANK
    
    os.makedirs("log", exist_ok=True)
    log_file = os.path.join("log", "reranking.log.md")
    
    mode = "w" if FIRST_RERANK else "a"
    FIRST_RERANK = False
    
    with open(log_file, mode, encoding="utf-8") as f:
        f.write(f"\n\n---\n\n# Reranking Query\n\n{query}\n\n")
        f.write(f"## Scoring {len(documents)} chunks individually\n\n")
    
    scores = []
    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        chunk_prompt = RERANKING_TEMPLATE.format(
            query=query,
            file=meta['file'],
            chunk=doc[:500]
        )
        
        result = subprocess.run(
            ["ollama", "run", model],
            input=chunk_prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        score_text = result.stdout.decode().strip()
        
        try:
            score = None
            for word in score_text.split():
                try:
                    score = int(word)
                    if 1 <= score <= 10:
                        break
                except ValueError:
                    continue
            
            if score is None:
                score = 2
            
            scores.append((score, i, doc, meta))
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"### Chunk {i+1}: {meta['file']} - Score: {score}/10\n\n")
                f.write(f"Response: `{score_text}`\n\n")
                f.write(f"```\n{doc}\n```\n\n")
                
        except Exception as e:
            scores.append((5, i, doc, meta))
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"### Chunk {i+1}: {meta['file']} - Error: {str(e)}\n\n")
    
    scores.sort(reverse=True, key=lambda x: x[0])
    
    reranked_docs = []
    reranked_metas = []
    
    for score, idx, doc, meta in scores[:chunks_to_select]:
        reranked_docs.append(doc)
        reranked_metas.append(meta)
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n## Selected Top {chunks_to_select} Chunks\n\n")
        for i, (score, idx, doc, meta) in enumerate(scores[:chunks_to_select], 1):
            f.write(f"{i}. **Score {score}/10** - {meta['file']}\n")
    
    return reranked_docs, reranked_metas
