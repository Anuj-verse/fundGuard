from __future__ import annotations

from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


BASE_DIR = Path(__file__).resolve().parents[1]

INDEX_DIR = BASE_DIR / "data" / "faiss_index"

DOCS_DIR = BASE_DIR / "data" / "compliance_docs"


def load_pdf_documents():

    documents = []

    for pdf_file in DOCS_DIR.rglob("*.pdf"):

        loader = PyPDFLoader(str(pdf_file))

        pages = loader.load()

        for page in pages:

            page.metadata["source"] = str(pdf_file)

            documents.append(page)

    return documents


def main() -> None:

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Existing fraud intelligence
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

    # Load compliance PDFs
    pdf_docs = load_pdf_documents()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
    )

    pdf_chunks = splitter.split_documents(pdf_docs)

    pdf_texts = [doc.page_content for doc in pdf_chunks]

    pdf_metadatas = [doc.metadata for doc in pdf_chunks]

    # Merge everything
    all_texts = texts + pdf_texts

    all_metadatas = metadatas + pdf_metadatas

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    store = FAISS.from_texts(
        texts=all_texts,
        embedding=embeddings,
        metadatas=all_metadatas
    )

    store.save_local(str(INDEX_DIR))

    print(f"Saved FAISS index to {INDEX_DIR}")

    print(f"Loaded {len(pdf_chunks)} PDF chunks")


if __name__ == "__main__":
    main()