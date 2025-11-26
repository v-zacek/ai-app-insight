# AI app insight

Lightweight AI assistant that explains how application works from user perspective.

Assistant indexes the project, converts codebase into vector embeddings using `nomic-embed-text` stored in chroma db to provide context aware answers. Local small LLM `llama3.2:3b` is used to answer questions.

Project is purely an experimental playground for testing how a locally running LLM behaves together with basic RAG/embedding techniques.