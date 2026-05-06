from __future__ import annotations

from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


BASE_DIR = Path(__file__).resolve().parents[1]
INDEX_DIR = BASE_DIR / "data" / "faiss_index"


def main() -> None:
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    texts = [
        "Confirmed fraud case FC-1001: circular transfers across mule accounts, rapid cash-outs, and shared device fingerprints.",
        "Confirmed fraud case FC-1002: structuring of deposits below reporting thresholds with beneficiary risk concentration.",
        "FIU-IND STR guidance: describe suspicious activity, the transaction chain, parties involved, and indicators supporting suspicion.",
        "RBI fraud typology note: sudden changes in transaction velocity, repeated beneficiaries, and new account burst activity may indicate mule behavior.",
    ]
    metadatas = [
        {"case_id": "FC-1001", "source": "confirmed_case"},
        {"case_id": "FC-1002", "source": "confirmed_case"},
        {"case_id": "FIU-STR-GUIDE", "source": "regulatory_guidance"},
        {"case_id": "RBI-TYPOLOGY-001", "source": "regulatory_guidance"},
    ]

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    store = FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)
    store.save_local(str(INDEX_DIR))
    print(f"Saved FAISS index to {INDEX_DIR}")


if __name__ == "__main__":
    main()
