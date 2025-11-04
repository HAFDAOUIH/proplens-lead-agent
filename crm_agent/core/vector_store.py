from typing import List, Dict, Any, Optional
import logging
import chromadb
from chromadb.config import Settings
from crm_agent.core.embeddings import MiniLMEmbedder


class ChromaStore:
    def __init__(self, persist_dir: str, collection: str = "brochures", embed_model: str = "all-MiniLM-L6-v2"):
        # Silence noisy telemetry warnings from Chroma/posthog in dev
        logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)
        logging.getLogger("posthog").setLevel(logging.CRITICAL)
        # Use PersistentClient instead of Client for persistence!
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(collection)
        self.embedder = MiniLMEmbedder(model_name=embed_model)

    def upsert(self, chunks: List[Dict[str, Any]]) -> int:
        ids, docs, metas, embeds = [], [], [], []
        for c in chunks:
            ids.append(c["id"])
            docs.append(c["text"])
            metas.append(c["metadata"])
            embeds.append(c["embedding"])
        if ids:
            self.collection.upsert(ids=ids, documents=docs, embeddings=embeds, metadatas=metas)
        return len(ids)

    def search(self, query: str, k: int = 4, project_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search using manual embedding since we provide embeddings in upsert."""
        where = {"project_name": project_name} if project_name else None
        query_embedding = self.embedder.embed([query])[0]
        res = self.collection.query(query_embeddings=[query_embedding], n_results=k, where=where)
        out = []
        for i in range(len(res.get("ids", [[]])[0])):
            out.append({
                "id": res["ids"][0][i],
                "text": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i] if "distances" in res else None
            })
        return out

    def count(self) -> int:
        """Return total number of chunks in collection."""
        return self.collection.count()