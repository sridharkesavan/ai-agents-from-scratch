import chromadb
from chromadb.utils import embedding_functions
import anthropic
from dotenv import load_dotenv

load_dotenv()

def main():
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path="chroma_db")
    collection = client.get_collection(name="my_documents", embedding_function=embed_fn)

    llm = anthropic.Anthropic()

    while True:
        question = input("\nAsk a question (or 'quit'): ")
        if question.lower() == "quit":
            break

        # Retrieval
        results = collection.query(query_texts=[question], n_results=4)
        chunks = results["documents"][0]
        sources = results["metadatas"][0]

        context = "\n\n".join(
            f"[Source: {src['source']}, chunk {src['chunk_index']}]\n{chunk}"
            for chunk, src in zip(chunks, sources)
        )

        # Generation — grounded in retrieved context only
        prompt = f"""Answer the question using ONLY the context below. 
If the context doesn't contain the answer, say so — don't make anything up.
Cite the source filename for any claim you make.

Context:
{context}

Question: {question}"""

        response = llm.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        print(f"\n{response.content[0].text}")
        print(f"\n(Retrieved from: {', '.join(set(s['source'] for s in sources))})")

if __name__ == "__main__":
    main()