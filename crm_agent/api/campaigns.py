"""
Campaign API - Create and manage outreach campaigns.
"""
from ninja import Router, Query
from ninja.errors import HttpError
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os

from django.shortcuts import get_object_or_404
from coreapp.models import Campaign, Message, Lead, Thread, ThreadMessage
from crm_agent.core.campaign_service import CampaignService
from crm_agent.agent.graph import build_graph

router = Router(tags=["campaigns"])

# Initialize campaign service
CHROMA_DIR = os.getenv("CHROMA_DIR", "/home/hafdaoui/Documents/Proplens/crm_agent/data/chroma")
campaign_service = CampaignService(chroma_dir=CHROMA_DIR)

# Initialize agent graph for reply handling
agent_graph = build_graph()


class CreateCampaignRequest(BaseModel):
    """Campaign creation request with lead targeting."""
    name: str
    project: str
    channel: str = "email"
    offer_text: str = ""
    lead_ids: List[int]

    class Config:
        schema_extra = {
            "example": {
                "name": "Beachgate Launch Campaign",
                "project": "Beachgate by Address",
                "channel": "email",
                "offer_text": "Exclusive 5% early bird discount",
                "lead_ids": [1, 2, 3]
            }
        }


class LeadReplyRequest(BaseModel):
    """Lead reply message."""
    message: str

    class Config:
        schema_extra = {
            "example": {
                "message": "I am interested in scheduling a site visit. What times are available?"
            }
        }


@router.post("/campaigns", summary="Create Campaign with AI-Generated Emails", description="""
Create a new outreach campaign with AI-generated personalized emails.

The system will:
1. Create a Campaign record
2. For each lead, generate a unique personalized email using:
   - Lead profile (name, budget, unit preferences, conversation history)
   - RAG-retrieved property information from brochures
   - Campaign offer text
3. Mock "send" the messages (set delivered=True)
4. Return summary with sample messages

**Personalization includes:**
- Lead name and custom greeting
- Budget-specific unit recommendations
- Unit type preferences matching lead profile
- Property features relevant to lead
- Campaign offer integration
""")
def create_campaign(request, payload: CreateCampaignRequest):
    """
    Create a campaign and generate personalized messages for each lead.

    Workflow:
    1. Create Campaign record
    2. For each lead:
       - Fetch lead profile
       - Generate personalized email using RAG + lead data
       - Save Message record
       - Mock "send" (set delivered=True)
    3. Return summary with sample messages
    """
    if not payload.lead_ids or len(payload.lead_ids) == 0:
        raise HttpError(400, "At least one lead_id required")

    # Create campaign
    campaign = Campaign.objects.create(
        name=payload.name,
        project=payload.project,
        channel=payload.channel,
        offer_text=payload.offer_text
    )

    messages_created = []
    errors = []

    for lead_id in payload.lead_ids:
        try:
            lead = Lead.objects.get(id=lead_id)

            # Convert lead to dict for service
            lead_dict = {
                "name": lead.name,
                "email": lead.email,
                "unit_type": lead.unit_type,
                "budget_min": float(lead.budget_min) if lead.budget_min else None,
                "budget_max": float(lead.budget_max) if lead.budget_max else None,
                "last_conversation_summary": lead.last_conversation_summary,
            }

            # Generate personalized email
            email_data = campaign_service.generate_email(
                lead=lead_dict,
                project=payload.project,
                offer_text=payload.offer_text,
                k=3
            )

            # Save message
            message = Message.objects.create(
                campaign=campaign,
                lead=lead,
                subject=email_data["subject"],
                body=email_data["body"],
                delivered=True  # Mock delivery
            )

            messages_created.append({
                "lead_id": lead.id,
                "lead_name": lead.name,
                "lead_email": lead.email,
                "subject": message.subject,
                "body": message.body[:200] + "..." if len(message.body) > 200 else message.body
            })

        except Lead.DoesNotExist:
            errors.append({"lead_id": lead_id, "error": "Lead not found"})
        except Exception as e:
            errors.append({"lead_id": lead_id, "error": str(e)})

    return {
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "project": campaign.project,
        "sent_count": len(messages_created),
        "error_count": len(errors),
        "sample_messages": messages_created[:3],  # First 3 for preview
        "errors": errors if errors else None
    }


@router.post("/campaigns/{campaign_id}/lead/{lead_id}/reply")
def handle_lead_reply(request, campaign_id: int, lead_id: int, payload: LeadReplyRequest):
    """
    Handle a reply from a lead in a campaign.

    Workflow:
    1. Find or create Thread for this campaign + lead
    2. Save lead's message as ThreadMessage (role="lead")
    3. Route lead's message through agent graph
    4. Save agent's response as ThreadMessage (role="agent")
    5. Update Thread.updated_at
    6. Return agent response
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    lead = get_object_or_404(Lead, id=lead_id)

    # Find or create thread
    thread, created = Thread.objects.get_or_create(
        campaign=campaign,
        lead=lead,
        defaults={
            "initial_message": Message.objects.filter(campaign=campaign, lead=lead).first()
        }
    )

    # Save lead's message
    lead_message = ThreadMessage.objects.create(
        thread=thread,
        role="lead",
        content=payload.message
    )

    # Route through agent graph
    from crm_agent.agent.state import AgentState
    import uuid

    # Use thread_id for conversation continuity
    thread_id = f"campaign_{campaign_id}_lead_{lead_id}"
    config = {"configurable": {"thread_id": thread_id}}

    state = AgentState(query=payload.message)

    try:
        result = agent_graph.invoke(state, config=config)
        agent_response = result.get("answer", "I'm sorry, I couldn't process that request.")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Agent routing error: {str(e)}")
        agent_response = "I apologize, but I'm having trouble processing your message. Could you please rephrase?"

    # Save agent's response
    agent_message = ThreadMessage.objects.create(
        thread=thread,
        role="agent",
        content=agent_response
    )

    # Mark message as replied
    initial_msg = Message.objects.filter(campaign=campaign, lead=lead).first()
    if initial_msg:
        initial_msg.replied = True
        initial_msg.save()

    return {
        "thread_id": thread.id,
        "lead_message": lead_message.content,
        "agent_response": agent_message.content,
        "created_at": agent_message.created_at.isoformat()
    }


@router.get("/campaigns/{campaign_id}/followups", summary="Get Campaign Followups", description="""
Get all conversation threads for a campaign.

Returns a list of threads with:
- Lead contact information
- Message count and recent messages (last 5)
- Last updated timestamp
- Goal achievement status
- Proposed date for site visit/meeting

Use this endpoint to build a "Followups" screen showing all ongoing conversations.
""")
def get_followups(request, campaign_id: int):
    """
    Get all conversation threads for a campaign (followups screen).

    Returns threads with latest message and goal status.
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    threads = Thread.objects.filter(campaign=campaign).select_related("lead").prefetch_related("thread_messages")

    followups = []
    for thread in threads:
        latest_messages = thread.thread_messages.all()[:5]  # Last 5 messages

        followups.append({
            "thread_id": thread.id,
            "lead_name": thread.lead.name,
            "lead_email": thread.lead.email,
            "lead_phone": thread.lead.phone,
            "message_count": thread.thread_messages.count(),
            "last_updated": thread.updated_at.isoformat(),
            "goal_achieved": thread.goal_achieved,
            "goal_type": thread.goal_type,
            "proposed_date": thread.proposed_date.isoformat() if thread.proposed_date else None,
            "recent_messages": [
                {
                    "role": msg.role,
                    "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in latest_messages
            ]
        })

    return {
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "total_threads": len(followups),
        "followups": followups
    }


@router.get("/campaigns/{campaign_id}/metrics", summary="Get Campaign Metrics", description="""
Get campaign performance metrics and KPIs.

**Metrics returned:**
- `leads_shortlisted`: Total leads targeted in campaign
- `messages_sent`: Total messages sent
- `unique_leads_responded`: Number of unique leads who replied
- `goals_achieved_count`: Number of threads where goal was achieved (site visit scheduled, etc.)

Use this to build a campaign dashboard showing performance and engagement.
""")
def get_campaign_metrics(request, campaign_id: int):
    """
    Get campaign performance metrics.

    Returns:
    - leads_shortlisted: Total leads targeted
    - messages_sent: Total messages sent
    - unique_leads_responded: Number of leads who replied
    - goals_achieved_count: Number of threads with goals achieved
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)

    messages_sent = Message.objects.filter(campaign=campaign).count()
    leads_shortlisted = Message.objects.filter(campaign=campaign).values('lead').distinct().count()

    # Count unique leads who have replied
    threads_with_replies = Thread.objects.filter(
        campaign=campaign,
        thread_messages__role="lead"
    ).distinct().count()

    # Count goals achieved
    goals_achieved = Thread.objects.filter(campaign=campaign, goal_achieved=True).count()

    return {
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "leads_shortlisted": leads_shortlisted,
        "messages_sent": messages_sent,
        "unique_leads_responded": threads_with_replies,
        "goals_achieved_count": goals_achieved
    }
