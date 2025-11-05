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


class Campaign(models.Model):
    """Represents an outreach campaign targeting specific leads."""
    CHANNEL_CHOICES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("whatsapp", "WhatsApp"),
    ]

    name = models.CharField(max_length=200)
    project = models.CharField(max_length=200)  # Which project this campaign is promoting
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="email")
    offer_text = models.TextField(blank=True)  # Special offer or campaign message
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.project})"


class Message(models.Model):
    """Represents an individual message sent to a lead as part of a campaign."""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="messages")
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="messages")
    subject = models.CharField(max_length=300, blank=True)  # For emails
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    # Mock tracking fields (in real system would integrate with email service)
    delivered = models.BooleanField(default=True)
    opened = models.BooleanField(default=False)
    replied = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Message to {self.lead.name} in {self.campaign.name}"


class Thread(models.Model):
    """Represents a conversation thread between a lead and the agent."""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="threads")
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="threads")
    initial_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True)

    # Goal tracking
    goal_achieved = models.BooleanField(default=False)
    goal_type = models.CharField(max_length=100, blank=True)  # e.g., "schedule_visit", "request_brochure"
    proposed_date = models.DateField(null=True, blank=True)  # For site visit scheduling

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Thread: {self.lead.name} - {self.campaign.name}"


class ThreadMessage(models.Model):
    """Individual messages within a conversation thread."""
    ROLE_CHOICES = [
        ("lead", "Lead"),
        ("agent", "Agent"),
    ]

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="thread_messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:50]}..."