from ninja import Router, File, Query
from ninja.files import UploadedFile
from ninja.errors import HttpError
from dotenv import load_dotenv

import os
import hashlib
from typing import Optional

from pypdf import PdfReader

from crm_agent.core.pipelines.document_ingestion import DocumentIngestor
from crm_agent.core.vector_store import ChromaStore

load_dotenv()

router = Router(tags=["docs"])

CHROMA_DIR = os.getenv("CHROMA_DIR", "/home/hafdaoui/Documents/Proplens/crm_agent/data/chroma")
BROCHURES_DIR = os.getenv("BROCHURES_DIR", "/home/hafdaoui/Documents/Proplens/crm_agent/data/brochures")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
OCR_LANG = os.getenv("OCR_LANG", "eng")

os.makedirs(CHROMA_DIR, exist_ok=True)
os.makedirs(BROCHURES_DIR, exist_ok=True)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_pdf_title(path: str) -> Optional[str]:
    try:
        reader = PdfReader(path)
        meta = reader.metadata or {}
        # PyPDF may return keys like '/Title'
        for k, v in dict(meta).items():
            if k.lower().endswith("title") and v:
                title = str(v).strip()
                if title:
                    return title
    except Exception:
        return None
    return None


@router.post("/docs/upload")
def upload_brochures(request, files: list[UploadedFile] = File(...), project: str | None = None, force: bool | None = False):
    """Upload 1..n PDFs, require explicit project or PDF Title metadata.

    - Computes document_id = sha256(file).
    - If force=False and file already exists on disk, reuse; otherwise overwrite.
    - Ingests pages → chunks → embeddings → Chroma upsert.
    """
    ing = DocumentIngestor(persist_dir=CHROMA_DIR, embed_model=EMBED_MODEL, ocr_lang=OCR_LANG)
    total_ins, total_pages, total_ocr = 0, 0, 0
    results = []

    for f in files:
        if not f.name.lower().endswith(".pdf"):
            raise HttpError(400, "Only PDF brochures are accepted.")

        temp_path = os.path.join(BROCHURES_DIR, f.name)
        with open(temp_path, "wb") as out:
            for chunk in f.chunks():
                out.write(chunk)

        document_id = _sha256_file(temp_path)
        final_name = f"{document_id}.pdf"
        final_path = os.path.join(BROCHURES_DIR, final_name)

        if not force and os.path.exists(final_path):
            # already stored the same content; skip move
            os.remove(temp_path)
        else:
            # place by content hash for idempotence
            if os.path.exists(final_path):
                os.remove(final_path)
            os.replace(temp_path, final_path)

        # Enforce project name (required for proper source attribution)
        pj = project or _read_pdf_title(final_path)
        if not pj or not pj.strip():
            raise HttpError(
                400,
                f"Project name required for '{f.name}': "
                "Provide explicit ?project=... parameter or ensure PDF has Title metadata set."
            )

        # Normalize project name (trim whitespace, ensure consistency)
        pj = pj.strip()

        res = ing.ingest_pdf(final_path, pj)
        res.update({
            "document_id": document_id,
            "stored_path": final_path,
            "project_name": pj,
            "original_filename": f.name
        })
        total_ins += res["inserted_chunks"]
        total_pages += res["pages_processed"]
        total_ocr += res["ocr_pages"]
        results.append(res)

    return {
        "files": results,
        "inserted_chunks": total_ins,
        "pages_processed": total_pages,
        "ocr_pages": total_ocr,
    }


@router.get("/docs/search")
def search_docs(request, q: str = Query(...), k: int = Query(4)):
    """Semantic search over ingested brochures. k defaults to 4 if not provided.
    
    Optional query params:
    - project: filter by project name (omit to search all projects)
    """
    # Get project from raw query params to avoid Django Ninja parsing issues
    project = request.GET.get("project", "").strip()
    project_filter = project if project else None
    store = ChromaStore(persist_dir=CHROMA_DIR, collection="brochures", embed_model=EMBED_MODEL)
    hits = store.search(q, k=k, project_name=project_filter)
    return {"matches": hits}


@router.get("/docs/count")
def count_docs(request):
    """Debug endpoint: check how many chunks are in ChromaDB."""
    store = ChromaStore(persist_dir=CHROMA_DIR, collection="brochures", embed_model=EMBED_MODEL)
    count = store.collection.count()
    return {"total_chunks": count}


