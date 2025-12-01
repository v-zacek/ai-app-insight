# AI app insight

Lightweight AI assistant that explains how application works from user perspective.

Assistant indexes the project, splits codebase into AST based chunks. 
Chunks are then converted into vector embeddings using `nomic-embed-text` stored in chroma db to provide context aware answers.
Chunks are then reranked by LLM and used as context for question. Local small LLM `llama3.2:3b` is used to answer questions and rerank chunks.

Project is purely an experimental playground for testing how a locally running LLM behaves together with basic RAG/embedding techniques.

## Requirements

- Install ollama models from config.yml.
- Default `llama3.2:3b`, `nomic-embed-text`

## Usage

### 1. Configure
- set path to project and excluded dirs in config.yml
- if you need custom template create `prompt_template.custom.md` in project root. This will override default template.

### 2. Index your project
```bash
python index.py
```

### 3. Ask questions
```bash
python query.py "How can I change my password"

python query.py "What does the 'revert' button do on user detail?"
```