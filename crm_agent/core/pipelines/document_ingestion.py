import os
import hashlib
from typing import Dict

from crm_agent.core.pipelines.extractors import PdfExtractor
from crm_agent.core.pipelines.chunking import TextChunker
from crm_agent.core.embeddings import MiniLMEmbedder
from crm_agent.core.vector_store import ChromaStore


def _make_id(text: str, meta: Dict) -> str:
    key = f"{meta.get('project_name','')}|{meta.get('source','')}|{meta.get('page','')}|{text[:80]}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()


class DocumentIngestor:
    def __init__(self, persist_dir: str, embed_model: str = "all-MiniLM-L6-v2", ocr_lang: str = "eng"):
        self.extractor = PdfExtractor(ocr_lang=ocr_lang)
        self.chunker = TextChunker()
        self.embedder = MiniLMEmbedder(model_name=embed_model)
        self.store = ChromaStore(persist_dir=persist_dir, collection="brochures", embed_model=embed_model)

    def ingest_pdf(self, pdf_path: str, project_name: str) -> Dict:
        pages = self.extractor.extract_pages(pdf_path)
        chunks = self.chunker.chunk(pages, project_name=project_name, source=os.path.basename(pdf_path))

        # de-dup near identical chunks
        seen = set()
        uniq = []
        for c in chunks:
            h = _make_id(c["text"], c["metadata"])
            if h in seen:
                continue
            seen.add(h)
            c["id"] = h
            uniq.append(c)

        embeddings = self.embedder.embed([c["text"] for c in uniq])
        for c, emb in zip(uniq, embeddings):
            c["embedding"] = emb

        inserted = self.store.upsert(uniq)
        ocr_pages = sum(1 for p in pages if p.get("has_ocr"))
        return {"inserted_chunks": inserted, "pages_processed": len(pages), "ocr_pages": ocr_pages}


