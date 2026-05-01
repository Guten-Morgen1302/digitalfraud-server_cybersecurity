from __future__ import annotations

import os
from typing import Any


class FraudKnowledgeBase:
    def __init__(
        self,
        persist_directory: str = "fraud_sentinel/rag/chroma_store",
        collection_name: str = "securevista_fraud_patterns",
    ) -> None:
        try:
            import chromadb
            from chromadb.utils import embedding_functions
        except ImportError as exc:
            raise RuntimeError(
                "Install ML dependencies first: pip install -r requirements-ml.txt"
            ) from exc

        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_fn,
        )

    def add_pattern(
        self,
        pattern_text: str,
        fraud_type: str,
        severity: str,
        advice: str,
        pattern_id: str,
        source: str | None = None,
    ) -> None:
        metadata = {
            "fraud_type": fraud_type,
            "severity": severity,
            "advice": advice,
            "source": source or "manual",
        }
        self.collection.upsert(ids=[pattern_id], documents=[pattern_text], metadatas=[metadata])

    def query(self, text: str, n_results: int = 3) -> list[dict[str, Any]]:
        result = self.collection.query(query_texts=[text], n_results=n_results)
        matches: list[dict[str, Any]] = []
        for idx, doc_id in enumerate(result.get("ids", [[]])[0]):
            matches.append(
                {
                    "id": doc_id,
                    "text": result.get("documents", [[]])[0][idx],
                    "metadata": result.get("metadatas", [[]])[0][idx],
                    "distance": result.get("distances", [[]])[0][idx]
                    if result.get("distances")
                    else None,
                }
            )
        return matches
