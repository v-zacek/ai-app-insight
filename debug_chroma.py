import chromadb
import json
from datetime import datetime

client = chromadb.PersistentClient(path="./index")

md_lines = [
    "# Chroma Database Output\n",
    f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
    "---\n"
]

total_items = 0

for col in client.list_collections():
    print(f"Processing collection: {col.name}")
    data = col.get()
    
    md_lines.append(f"\n## Collection: {col.name}\n")
    md_lines.append(f"**Items:** {len(data['ids'])}\n")
    
    total_items += len(data['ids'])
    
    for i in range(len(data["ids"])):
        md_lines.append(f"\n### Item {i+1}\n")
        md_lines.append(f"**ID:** `{data['ids'][i]}`\n")
        
        if data["metadatas"] and data["metadatas"][i]:
            md_lines.append("\n**Metadata:**\n")
            md_lines.append("```json\n")
            md_lines.append(json.dumps(data["metadatas"][i], indent=2, ensure_ascii=False))
            md_lines.append("\n```\n")
        
        if data["documents"] and data["documents"][i]:
            md_lines.append("\n**Document:**\n")
            md_lines.append("```\n")
            md_lines.append(data["documents"][i])
            md_lines.append("\n```\n")

output_file = "chroma_output.md"
with open(output_file, "w", encoding="utf-8") as f:
    f.writelines(md_lines)

print(f"\nOutput saved to {output_file}")
print(f"Total collections: {len(client.list_collections())}")
print(f"Total items: {total_items}")