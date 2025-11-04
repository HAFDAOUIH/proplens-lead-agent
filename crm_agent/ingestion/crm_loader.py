from typing import Optional
import pandas as pd
from coreapp.models import Lead

# Excel headers → Lead model fields
HEADER_MAP = {
    "Lead ID": "crm_id",
    "Lead name": "name",
    "Email": "email",
    "Country code": "country_code",
    "Phone": "phone",
    "Project name": "project_enquired",
    "Unit type": "unit_type",
    "Min. Budget": "budget_min",
    "Max Budget": "budget_max",
    "Lead status": "status",
    "Last conversation date": "last_conversation_date",
    "Last conversation summary": "last_conversation_summary",
}

def _to_number(v):
    try:
        if pd.isna(v):
            return None
        return float(str(v).replace(",", "").strip())
    except Exception:
        return None

def _to_date(v):
    try:
        if pd.isna(v) or v == "":
            return None
        return pd.to_datetime(v, errors="coerce").date()
    except Exception:
        return None

def load_excel_to_db(path: str) -> int:
    # Force openpyxl engine for .xlsx and provide clearer errors for wrong file types
    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception as exc:
        raise ValueError(f"Failed to read Excel file. Ensure it's a valid .xlsx: {exc}")
    # Normalize headers by stripping spaces
    df = df.rename(columns={c: c.strip() for c in df.columns})

    rows = []
    for _, r in df.iterrows():
        payload = {}
        for src, dst in HEADER_MAP.items():
            if src not in df.columns:
                continue
            val = r.get(src)

            if dst in ("budget_min", "budget_max"):
                val = _to_number(val)
            elif dst == "last_conversation_date":
                val = _to_date(val)
            elif dst == "status" and isinstance(val, str):
                val = val.strip()
            elif isinstance(val, str):
                val = val.strip()

            payload[dst] = val
        if "name" in payload and "email" in payload:
            rows.append(Lead(**payload))

    if rows:
        Lead.objects.bulk_create(rows, ignore_conflicts=True)
    return len(rows)