from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.namespace_manager import get_embeddings, get_index


def build_vector_store(transcript: str, namespace: str) -> PineconeVectorStore:
    if not namespace:
        raise ValueError("namespace is required to build vector store")
    if not transcript or not transcript.strip():
        raise ValueError("transcript is empty — cannot build vector store")

    #print(f"[VectorStore] Building index for namespace: {namespace}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(transcript)

    if not chunks:
        raise ValueError("transcript produced zero chunks after splitting")

    docs = [
        Document(
            page_content=chunk,
            metadata={"chunk_index": i, "source": "video_transcript", "namespace": namespace},
        )
        for i, chunk in enumerate(chunks)
    ]
    ids = [f"{namespace}-chunk-{i}" for i in range(len(docs))]

    #print(f"[VectorStore] Inserting {len(docs)} document(s) into namespace: {namespace}")

    embeddings = get_embeddings()
    index = get_index()

    try:
        vector_store = PineconeVectorStore(
            index=index,
            embedding=embeddings,
            namespace=namespace,
        )
        vector_store.add_documents(documents=docs, ids=ids)
        #print(f"[VectorStore] Successfully inserted {len(docs)} vectors into namespace: {namespace}")
    except Exception as e:
        #print(f"[VectorStore] Pinecone insertion failed for namespace {namespace}: {e}")
        raise

    return vector_store


def load_vector_store(namespace: str) -> PineconeVectorStore:
    if not namespace:
        raise ValueError("namespace is required to load vector store")

    #print(f"[VectorStore] Loading vector store for namespace: {namespace}")

    embeddings = get_embeddings()
    index = get_index()
    try:
        vector_store = PineconeVectorStore(
            index=index,
            embedding=embeddings,
            namespace=namespace,
        )
        #print(f"[VectorStore] Loaded vector store for namespace: {namespace}")
        return vector_store
    except Exception as e:
        #print(f"[VectorStore] Failed to load vector store for namespace {namespace}: {e}")
        raise


def get_retriever(vector_store: PineconeVectorStore, k: int = 4):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )
