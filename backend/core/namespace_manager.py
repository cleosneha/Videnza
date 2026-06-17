import os
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from dotenv import load_dotenv
from langchain_mistralai import MistralAIEmbeddings
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "calmhive-video-assistant")
INDEX_HOST = os.getenv("PINECONE_INDEX_HOST", "")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
EMBEDDING_MODEL = "mistral-embed"

REGISTRY_NAMESPACE = "__registry__"
REGISTRY_ID_PREFIX = "namespace:"
SESSION_NAMESPACE_KEY = "pinecone_namespace"
NAMESPACE_TTL_SECONDS = int(os.getenv("PINECONE_NAMESPACE_TTL_SECONDS", str(24 * 60 * 60)))


def _validate_mistral_api_key() -> str:
    key = os.getenv("MISTRAL_API_KEY")
    if not key:
        raise RuntimeError(
            "MISTRAL_API_KEY is not set. "
            "Add MISTRAL_API_KEY to your .env file or environment variables."
        )
    return key


def get_embeddings() -> MistralAIEmbeddings:
    _validate_mistral_api_key()
    return MistralAIEmbeddings(model=EMBEDDING_MODEL)


def get_pinecone_client() -> Pinecone:
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY is not set in the environment.")
    return Pinecone(api_key=api_key)


def _get_embedding_dimension(embeddings: MistralAIEmbeddings) -> int:
    sample_vector = embeddings.embed_query("dimension check")
    return len(sample_vector)


def _wait_for_index_ready(pc: Pinecone, index_name: str, timeout_seconds: int = 60) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        description = pc.describe_index(index_name)
        status = getattr(description, "status", None)

        if isinstance(status, dict) and status.get("ready"):
            return

        if hasattr(status, "ready") and status.ready:
            return

        time.sleep(2)

    raise TimeoutError(f"Pinecone index '{index_name}' was not ready within {timeout_seconds} seconds.")


def ensure_index() -> None:
    embeddings = get_embeddings()
    embedding_dimension = _get_embedding_dimension(embeddings)
    pc = get_pinecone_client()

    if not pc.has_index(INDEX_NAME):
        pc.create_index(
            name=INDEX_NAME,
            vector_type="dense",
            dimension=embedding_dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
            deletion_protection="disabled",
            tags={"app": "video-assistant"},
        )
        _wait_for_index_ready(pc, INDEX_NAME)
        return

    description = pc.describe_index(INDEX_NAME)
    existing_dimension = getattr(description, "dimension", None)
    if existing_dimension is None and isinstance(description, dict):
        existing_dimension = description.get("dimension")

    if existing_dimension is not None and existing_dimension != embedding_dimension:
        raise ValueError(
            f"Pinecone index '{INDEX_NAME}' has dimension {existing_dimension}, "
            f"but '{EMBEDDING_MODEL}' returns {embedding_dimension}. "
            "Use a different index name or recreate the index with the correct dimension."
        )


def _normalize_host(index_host: str) -> str:
    return urlparse(index_host).netloc or index_host


# ── Embedding-free index helpers (for namespace operations) ────────────────────


def _index_exists() -> bool:
    pc = get_pinecone_client()
    return pc.has_index(INDEX_NAME)


def _get_describe_dimension() -> int | None:
    pc = get_pinecone_client()
    try:
        description = pc.describe_index(INDEX_NAME)
        dimension = getattr(description, "dimension", None)
        if dimension is None and isinstance(description, dict):
            dimension = description.get("dimension")
        return int(dimension) if dimension is not None else None
    except Exception:
        return None


def _get_index_no_ensure():
    pc = get_pinecone_client()
    normalized_host = _normalize_host(INDEX_HOST)
    return pc.Index(host=normalized_host) if normalized_host else pc.Index(INDEX_NAME)


def get_index():
    ensure_index()
    return _get_index_no_ensure()


def get_index_dimension() -> int:
    pc = get_pinecone_client()
    description = pc.describe_index(INDEX_NAME)
    dimension = getattr(description, "dimension", None)
    if dimension is None and isinstance(description, dict):
        dimension = description.get("dimension")
    if dimension is None:
        raise ValueError(f"Could not determine dimension for Pinecone index '{INDEX_NAME}'.")
    return int(dimension)


# ── Registry helpers (embedding-free) ──────────────────────────────────────────


def _registry_record_id(namespace: str) -> str:
    return f"{REGISTRY_ID_PREFIX}{namespace}"


def _registry_vector(dimension: int | None = None) -> list[float]:
    if dimension is None:
        dimension = _get_describe_dimension()
    if dimension is None:
        dimension = get_index_dimension()
    return [0.0] * dimension


def generate_namespace() -> str:
    ns = f"session-{uuid.uuid4().hex}"
    #print(f"[Namespace] Generated: {ns}")
    return ns


def get_session_namespace(session_state) -> str | None:
    ns = session_state.get(SESSION_NAMESPACE_KEY)
    #print(f"[Namespace] get_session_namespace: {ns}")
    return ns


def ensure_session_namespace(session_state) -> str:
    namespace = get_session_namespace(session_state)
    if namespace:
        return namespace

    namespace = generate_namespace()
    session_state[SESSION_NAMESPACE_KEY] = namespace
    #print(f"[Namespace] ensure_session_namespace: set to {namespace}")
    return namespace


def set_session_namespace(session_state, namespace: str) -> str:
    session_state[SESSION_NAMESPACE_KEY] = namespace
    #print(f"[Namespace] set_session_namespace: {namespace}")
    return namespace


def register_namespace(namespace: str) -> None:
    if not namespace:
        print("[Namespace] register_namespace: skipping — empty namespace")
        return

    if not _index_exists():
        print("[Namespace] register_namespace: Pinecone index does not exist yet — skipping")
        return

    index = _get_index_no_ensure()
    created_at = int(time.time())
    record_id = _registry_record_id(namespace)
    dimension = _get_describe_dimension()
    try:
        index.upsert(
            vectors=[
                {
                    "id": record_id,
                    "values": _registry_vector(dimension),
                    "metadata": {
                        "namespace": namespace,
                        "created_at": created_at,
                        "created_at_iso": datetime.fromtimestamp(created_at, tz=timezone.utc).isoformat(),
                    },
                }
            ],
            namespace=REGISTRY_NAMESPACE,
        )
        print(f"[Namespace] Registered: {namespace} (id={record_id})")
    except Exception as e:
        print(f"[Namespace] Failed to register {namespace}: {e}")


def delete_namespace_registry(namespace: str) -> None:
    if not namespace:
        print("[Namespace] delete_namespace_registry: skipping — empty namespace")
        return
    if not _index_exists():
        print("[Namespace] delete_namespace_registry: index does not exist — skipping")
        return
    index = _get_index_no_ensure()
    record_id = _registry_record_id(namespace)
    try:
        index.delete(ids=[record_id], namespace=REGISTRY_NAMESPACE)
        print(f"[Namespace] Registry entry deleted: {record_id}")
    except Exception as e:
        print(f"[Namespace] Failed to delete registry entry {record_id}: {e}")


def delete_namespace(namespace: str, remove_registry: bool = True) -> None:
    if not namespace:
        print("[Namespace] delete_namespace: skipping — empty namespace")
        return

    if not _index_exists():
        print("[Namespace] delete_namespace: index does not exist — skipping")
        return

    print(f"[Namespace] Deleting all vectors in namespace: {namespace}")
    index = _get_index_no_ensure()
    try:
        index.delete(delete_all=True, namespace=namespace)
        print(f"[Namespace] Deleted namespace: {namespace}")
    except Exception as e:
        print(f"[Namespace] Failed to delete vectors in {namespace}: {e}")

    if remove_registry:
        delete_namespace_registry(namespace)


def cleanup_expired_namespaces(exclude_namespaces: set[str] | None = None) -> list[str]:
    print("[Namespace] Starting cleanup of expired namespaces...")

    if not _index_exists():
        print("[Namespace] Cleanup: Pinecone index does not exist yet — nothing to clean")
        return []

    index = _get_index_no_ensure()
    excluded = exclude_namespaces or set()
    cutoff_timestamp = int(time.time()) - NAMESPACE_TTL_SECONDS
    print(f"[Namespace] Cleanup cutoff: {datetime.fromtimestamp(cutoff_timestamp, tz=timezone.utc).isoformat()}")

    expired_namespaces: list[str] = []

    try:
        stats = index.describe_index_stats()
    except Exception as e:
        print(f"[Namespace] Cleanup: failed to describe index stats: {e}")
        return expired_namespaces

    namespaces = getattr(stats, "namespaces", None)
    if namespaces is None and isinstance(stats, dict):
        namespaces = stats.get("namespaces", {})

    registry_info = namespaces.get(REGISTRY_NAMESPACE, {}) if namespaces else {}
    registry_count = registry_info.get("vector_count", 0) if isinstance(registry_info, dict) else 0
    if registry_count == 0:
        print("[Namespace] Cleanup: no registry entries found")
        return expired_namespaces

    dimension = _get_describe_dimension()

    try:
        query_response = index.query(
            vector=_registry_vector(dimension),
            top_k=registry_count,
            namespace=REGISTRY_NAMESPACE,
            include_metadata=True,
            filter={"created_at": {"$lt": cutoff_timestamp}},
        )
    except Exception as e:
        print(f"[Namespace] Cleanup: registry query failed: {e}")
        return expired_namespaces

    for match in query_response.matches:
        metadata = getattr(match, "metadata", {}) or {}
        namespace = metadata.get("namespace")
        if namespace and namespace != REGISTRY_NAMESPACE and namespace not in excluded:
            expired_namespaces.append(namespace)

    print(f"[Namespace] Cleanup: found {len(expired_namespaces)} expired namespace(s)")

    for namespace in expired_namespaces:
        delete_namespace(namespace, remove_registry=True)

    if expired_namespaces:
        print(f"[Namespace] Cleanup complete: removed {len(expired_namespaces)} namespace(s)")
    else:
        print("[Namespace] Cleanup complete: no expired namespaces to remove")

    return expired_namespaces


def reset_session_namespace(session_state, register: bool = True) -> str:
    current_namespace = get_session_namespace(session_state)
    if current_namespace:
        print(f"[Namespace] Resetting: replacing namespace {current_namespace}")
        delete_namespace(current_namespace, remove_registry=True)
    else:
        print("[Namespace] Resetting: no current namespace to delete")

    new_namespace = generate_namespace()
    set_session_namespace(session_state, new_namespace)
    if register:
        register_namespace(new_namespace)
    print(f"[Namespace] Reset complete: active namespace is now {new_namespace}")
    return new_namespace
