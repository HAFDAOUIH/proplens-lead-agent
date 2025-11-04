from ninja import Router, File
from ninja.files import UploadedFile
from ninja.errors import HttpError
from typing import List

from crm_agent.core.schemas import ImportResult, ShortlistFilters
from crm_agent.ingestion.crm_loader import load_excel_to_db
from crm_agent.core.services import shortlist_leads

router = Router(tags=["leads"])

@router.post("/leads/import", response=ImportResult)
def import_leads(request, file: UploadedFile = File(...)):
    import tempfile, os
    # Basic validation: only accept .xlsx files
    filename = getattr(file, "name", "").lower()
    if not filename.endswith(".xlsx"):
        raise HttpError(400, "Please upload an .xlsx Excel file (not doc/docx/pdf).")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)
        temp_path = tmp.name
    try:
        inserted = load_excel_to_db(temp_path)
        return {"inserted": inserted}
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass

@router.post("/leads/shortlist")
def shortlist(request, payload: ShortlistFilters):
    selected = [
        v for v in [
            payload.project_enquired,
            payload.budget_min,
            payload.budget_max,
            (payload.unit_type if payload.unit_type else None),
            payload.status,
            payload.date_from,
            payload.date_to,
        ] if v not in (None, [], "")
    ]
    if len(selected) < 2:
        raise HttpError(400, "Provide at least two filters.")

    qs = shortlist_leads(
        project_enquired=payload.project_enquired,
        budget_min=payload.budget_min,
        budget_max=payload.budget_max,
        unit_types=payload.unit_type,
        status=payload.status,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )
    leads = list(qs.values("id", "name", "email"))
    return {"count": len(leads), "leads": leads}