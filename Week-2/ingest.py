import os
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

DOCS_DIR = "documents"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

def load_text_from_file(path: str) -> str:
    if path.endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif path.endswith((".md", ".txt")):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def chunk_text(text: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]

def main():
    # Local embedding model — free, runs on CPU, no API key needed
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    client = chromadb.PersistentClient(path="chroma_db")
    collection = client.get_or_create_collection(
        name="my_documents",
        embedding_function=embed_fn
    )

    doc_id = 0
    for filename in os.listdir(DOCS_DIR):
        filepath = os.path.join(DOCS_DIR, filename)
        print(f"Processing {filename}...")
        text = load_text_from_file(filepath)
        if not text:
            continue

        chunks = chunk_text(text)
        ids = [f"{filename}-{i}" for i in range(len(chunks))]
        metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]

        collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        print(f"  -> {len(chunks)} chunks indexed")
        doc_id += 1

    print(f"\nDone. Total chunks in collection: {collection.count()}")

if __name__ == "__main__":
    main()