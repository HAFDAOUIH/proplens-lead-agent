from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field, EmailStr

class LeadOut(BaseModel):
    id: int
    name: str
    email: EmailStr

class ImportResult(BaseModel):
    inserted: int

class ShortlistFilters(BaseModel):
    project_enquired: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    unit_type: Optional[List[str]] = Field(default=None, description="List of unit types to include")
    status: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None

class SearchQuery(BaseModel):
    q: str = Field(..., description="Search query string")
    k: int = Field(4, ge=1, le=20, description="Number of results to return")
    project: str = Field("", description="Filter by project name (empty = no filter)")

class T2SQLQuery(BaseModel):
    question: str = Field(..., description="Natural language question to convert to SQL")