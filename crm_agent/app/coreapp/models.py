from django.db import models

# Create your models here.
from django.db import models

class Lead(models.Model):
    STATUS_CHOICES = [
        ("New", "New"),
        ("Connected", "Connected"),
        ("Qualified", "Qualified"),
        ("Disqualified", "Disqualified"),
        ("FollowUp", "FollowUp"),
    ]

    # Optional CRM identifier from the spreadsheet
    crm_id = models.CharField(max_length=64, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    country_code = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    unit_type = models.CharField(max_length=100, blank=True)  # e.g., "2 bed"
    budget_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="New")
    last_conversation_date = models.DateField(null=True, blank=True)
    last_conversation_summary = models.TextField(blank=True)
    project_enquired = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"