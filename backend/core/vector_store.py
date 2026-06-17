from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.namespace_manager import get_embeddings, get_index


def build_vector_store(transcript: str, namespace: str) -> str:
    if not namespace:
        raise ValueError("namespace is required to build vector store")
    if not transcript or not transcript.strip():
        raise ValueError("transcript is empty — cannot build vector store")

    print(f"[VectorStore] Building index for namespace: {namespace}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(transcript)

    if not chunks:
        raise ValueError("transcript produced zero chunks after splitting")

    print(f"[VectorStore] Inserting {len(chunks)} chunks into namespace: {namespace}")

    embeddings = get_embeddings()
    index = get_index()

    embedding_vectors = embeddings.embed_documents(chunks)

    vectors = [
        {
            "id": f"{namespace}-chunk-{i}",
            "values": embedding_vectors[i],
            "metadata": {
                "text": chunk,
                "chunk_index": i,
                "source": "video_transcript",
                "namespace": namespace,
            },
        }
        for i, chunk in enumerate(chunks)
    ]

    try:
        index.upsert(vectors=vectors, namespace=namespace)
        print(f"[VectorStore] Successfully inserted {len(vectors)} vectors into namespace: {namespace}")
    except Exception as e:
        print(f"[VectorStore] Pinecone insertion failed for namespace {namespace}: {e}")
        raise

    return namespace


def load_vector_store(namespace: str) -> str:
    if not namespace:
        raise ValueError("namespace is required to load vector store")
    print(f"[VectorStore] Using namespace: {namespace}")
    return namespace


def get_retriever(namespace: str, k: int = 4):
    embeddings = get_embeddings()
    index = get_index()

    def retrieve(query: str) -> list[Document]:
        query_vector = embeddings.embed_query(query)
        results = index.query(
            vector=query_vector,
            top_k=k,
            namespace=namespace,
            include_metadata=True,
            include_values=False,
        )
        docs = []
        for match in results.matches:
            metadata = match.metadata or {}
            text = metadata.pop("text", "")
            docs.append(Document(page_content=text, metadata=metadata))
        return docs

    return RunnableLambda(retrieve)
