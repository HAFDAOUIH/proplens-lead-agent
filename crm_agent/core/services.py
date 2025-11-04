from typing import Iterable, Tuple
from datetime import date
from functools import reduce
from django.db.models import Q, QuerySet
from coreapp.models import Lead

def shortlist_leads(
    project_enquired=None,
    budget_min=None,
    budget_max=None,
    unit_types=None,
    status=None,
    date_from: date = None,
    date_to: date = None,
) -> QuerySet:
    qs = Lead.objects.all()
    if project_enquired:
        qs = qs.filter(project_enquired__icontains=project_enquired)
    if budget_min is not None:
        qs = qs.filter(budget_max__gte=budget_min)  # lead can afford at least min
    if budget_max is not None:
        qs = qs.filter(budget_min__lte=budget_max)
    if unit_types:
        cleaned = [str(u).strip() for u in unit_types if u is not None and str(u).strip() != ""]
        if cleaned:
            # OR across variants, case-insensitive substring
            qs = qs.filter(reduce(lambda a, b: a | b, [Q(unit_type__icontains=u) for u in cleaned]))
    if status:
        qs = qs.filter(status__iexact=str(status).strip())
    if date_from:
        qs = qs.filter(last_conversation_date__gte=date_from)
    if date_to:
        qs = qs.filter(last_conversation_date__lte=date_to)
    return qs