import ollama
import faiss
import numpy as np

def chunk_text(text: str) -> list[str]:
    chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
    return chunks

def build_index(documents: list[str]):
    embeddings = []
    for d in documents:
        r = ollama.embed(model="nomic-embed-text", input=d)
        embeddings.append(r["embeddings"][0])
    embeddings_np = np.array(embeddings, dtype="float32")
    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)
    return index

def answer_question(question: str, index, documents: list[str], k: int = 2) -> str:
    q_embedding = ollama.embed(model="nomic-embed-text", input=question)["embeddings"][0]
    q_embedding_np = np.array([q_embedding], dtype="float32")
    distances, indices = index.search(q_embedding_np, k)
    retrieved_docs = [documents[i] for i in indices[0]]
    context = "\n".join(retrieved_docs)
    final_prompt = f"""
Answer the question using ONLY the context below. If the context doesn't contain the answer, say so.

Context:
{context}

Question: {question}
"""
    resp = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": final_prompt}])
    return resp["message"]["content"]

# Load and chunk the real document FIRST
with open("docs/architecture.md", "r", encoding="utf-8") as f:
    text = f.read()

documents = chunk_text(text)
print(f"Number of chunks: {len(documents)}")

# Debug: find which chunk contains our target sentence
for i, c in enumerate(documents):
    if "Layer definitions" in c:
        print(f"Found in chunk {i}:")
        print(c)

# Build index from the REAL chunks (not toy data)
index = build_index(documents)

# Now ask questions
print(answer_question("what does the Bronze layer do?", index, documents, k=4))
print(answer_question("what does the Silver layer do?", index, documents, k=4))