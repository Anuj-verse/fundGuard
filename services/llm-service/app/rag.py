from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


BASE_DIR = Path(__file__).resolve().parents[1]
INDEX_DIR = Path(BASE_DIR, "data", "faiss_index")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def load_vectorstore(index_dir: Path | str = INDEX_DIR) -> FAISS:
    store_path = Path(index_dir)
    if not store_path.exists():
        raise FileNotFoundError(
            f"FAISS index not found at {store_path}. Run scripts/build_index.py first."
        )
    return FAISS.load_local(
        folder_path=str(store_path),
        embeddings=get_embeddings(),
        allow_dangerous_deserialization=True,
    )


def retrieve_similar_cases(query: str, k: int = 3, index_dir: Path | str = INDEX_DIR) -> list[dict[str, Any]]:
    vectorstore = load_vectorstore(index_dir)
    docs = vectorstore.similarity_search_with_score(query, k=k)
    results: list[dict[str, Any]] = []

    for doc, score in docs:
        metadata = dict(doc.metadata)
        case_id = metadata.get("case_id", "unknown-case")
        summary = doc.page_content.strip()
        similarity = 1.0 / (1.0 + float(score)) if score is not None else None
        results.append(
            {
                "case_id": case_id,
                "summary": summary,
                "similarity": similarity,
            }
        )

    return results
