"""
Pytest configuration and fixtures for CRM Agent tests.
"""
import pytest
import os
import sys
from pathlib import Path

# Add project root and parent to path
project_root = Path(__file__).parent.parent
crm_agent_root = project_root.parent
sys.path.insert(0, str(crm_agent_root))
sys.path.insert(0, str(project_root))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

import django
django.setup()

from django.test import Client
from rest_framework_simplejwt.tokens import RefreshToken
from coreapp.models import Lead, Campaign, Message


@pytest.fixture
def api_client():
    """Provide Django test client."""
    return Client()


@pytest.fixture
def auth_token(db):
    """Provide JWT authentication token."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Create test user
    user = User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )

    # Generate JWT token
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


@pytest.fixture
def authenticated_client(api_client, auth_token):
    """Provide authenticated API client."""
    api_client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {auth_token}'
    return api_client


@pytest.fixture
def sample_leads(db):
    """Create sample leads for testing."""
    leads = []
    for i in range(3):
        lead = Lead.objects.create(
            name=f"Test Lead {i+1}",
            email=f"lead{i+1}@test.com",
            phone=f"123456789{i}",
            unit_type="2 bed",
            budget_min=1000000 + (i * 100000),
            budget_max=1500000 + (i * 100000),
            status="Connected",
            project_enquired="Beachgate by Address",
            last_conversation_summary=f"Interested in 2-bed units with budget around AED 1.2M"
        )
        leads.append(lead)
    return leads


@pytest.fixture
def sample_campaign(db, sample_leads):
    """Create sample campaign for testing."""
    campaign = Campaign.objects.create(
        name="Test Campaign",
        project="Beachgate by Address",
        channel="email",
        offer_text="Special test offer"
    )

    # Create messages for leads
    for lead in sample_leads[:2]:
        Message.objects.create(
            campaign=campaign,
            lead=lead,
            subject=f"Test message for {lead.name}",
            body="Test message body",
            delivered=True
        )

    return campaign


@pytest.fixture
def chroma_test_dir(tmp_path):
    """Provide temporary ChromaDB directory for testing."""
    chroma_dir = tmp_path / "chroma"
    chroma_dir.mkdir()
    return str(chroma_dir)
