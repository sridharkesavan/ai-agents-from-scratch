from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

sentences = [
    "How do I cancel my subscription?",
    "Steps to terminate your plan",
    "What's the weather like today?"
]

embeddings = model.encode(sentences)
print("Shape:", embeddings.shape)

sim = cosine_similarity(embeddings)
print("Similarity matrix:")
print(sim)