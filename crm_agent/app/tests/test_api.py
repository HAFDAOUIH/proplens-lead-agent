"""
API endpoint tests for CRM Agent.
"""
import pytest
import json
from django.urls import reverse


class TestHealthAPI:
    """Test health check endpoint."""

    def test_health_endpoint(self, api_client):
        """Test health check returns 200."""
        response = api_client.get('/api/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'


class TestAuthAPI:
    """Test authentication endpoints."""

    def test_login_success(self, api_client, db):
        """Test successful login."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        User.objects.create_user(username='admin', password='admin')

        response = api_client.post(
            '/api/auth/login',
            data=json.dumps({'username': 'admin', 'password': 'admin'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data

    def test_login_invalid_credentials(self, api_client, db):
        """Test login with invalid credentials."""
        response = api_client.post(
            '/api/auth/login',
            data=json.dumps({'username': 'invalid', 'password': 'wrong'}),
            content_type='application/json'
        )
        assert response.status_code == 401


class TestLeadsAPI:
    """Test leads management endpoints."""

    def test_shortlist_leads_with_valid_filters(self, authenticated_client, sample_leads):
        """Test shortlist with 2+ filters."""
        response = authenticated_client.post(
            '/api/leads/shortlist',
            data=json.dumps({
                'project_enquired': 'Beachgate by Address',
                'status': 'Connected'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.json()
        assert data['count'] >= 1
        assert 'leads' in data

    def test_shortlist_leads_insufficient_filters(self, authenticated_client, sample_leads):
        """Test shortlist with less than 2 filters returns error."""
        response = authenticated_client.post(
            '/api/leads/shortlist',
            data=json.dumps({
                'status': 'Connected'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_shortlist_leads_without_auth(self, api_client):
        """Test shortlist without authentication returns 401."""
        response = api_client.post(
            '/api/leads/shortlist',
            data=json.dumps({
                'project_enquired': 'Test',
                'status': 'Connected'
            }),
            content_type='application/json'
        )
        assert response.status_code == 401


class TestDocsAPI:
    """Test document ingestion and search endpoints."""

    def test_docs_count(self, authenticated_client):
        """Test document count endpoint."""
        response = authenticated_client.get('/api/docs/count')
        assert response.status_code == 200
        data = response.json()
        assert 'total_chunks' in data
        assert isinstance(data['total_chunks'], int)

    def test_docs_search(self, authenticated_client):
        """Test semantic search endpoint."""
        response = authenticated_client.get('/api/docs/search?q=amenities&k=4')
        assert response.status_code == 200
        data = response.json()
        assert 'matches' in data


class TestT2SQLAPI:
    """Test Text-to-SQL endpoints."""

    def test_t2sql_query(self, authenticated_client, sample_leads):
        """Test natural language to SQL query."""
        response = authenticated_client.post(
            '/api/t2sql/query',
            data=json.dumps({
                'question': 'Count all leads'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.json()
        assert 'sql' in data
        assert 'rows' in data


class TestAgentAPI:
    """Test agent router endpoints."""

    def test_agent_query_rag_route(self, authenticated_client):
        """Test agent routes property questions to RAG."""
        response = authenticated_client.post(
            '/api/agent/query',
            data=json.dumps({
                'question': 'What amenities does Beachgate have?'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.json()
        assert data['route'] == 'rag'
        assert 'answer' in data
        assert 'sources' in data

    def test_agent_query_t2sql_route(self, authenticated_client, sample_leads):
        """Test agent routes analytics questions to T2SQL."""
        response = authenticated_client.post(
            '/api/agent/query',
            data=json.dumps({
                'question': 'How many leads do we have?'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.json()
        assert data['route'] == 't2sql'
        assert 'sql' in data

    def test_agent_query_clarify_route(self, authenticated_client):
        """Test agent clarify route for vague questions."""
        response = authenticated_client.post(
            '/api/agent/query',
            data=json.dumps({
                'question': 'What about that?'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.json()
        assert data['route'] == 'clarify'
        assert 'answer' in data


class TestCampaignsAPI:
    """Test campaign management endpoints."""

    def test_create_campaign(self, authenticated_client, sample_leads):
        """Test campaign creation with email generation."""
        response = authenticated_client.post(
            '/api/campaigns',
            data=json.dumps({
                'name': 'Test Campaign',
                'project': 'Beachgate by Address',
                'channel': 'email',
                'offer_text': 'Test offer',
                'lead_ids': [sample_leads[0].id, sample_leads[1].id]
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.json()
        assert data['sent_count'] == 2
        assert 'sample_messages' in data
        assert len(data['sample_messages']) == 2

    def test_campaign_metrics(self, authenticated_client, sample_campaign):
        """Test campaign metrics endpoint."""
        response = authenticated_client.get(f'/api/campaigns/{sample_campaign.id}/metrics')
        assert response.status_code == 200
        data = response.json()
        assert 'leads_shortlisted' in data
        assert 'messages_sent' in data
        assert 'unique_leads_responded' in data
        assert 'goals_achieved_count' in data

    def test_campaign_followups(self, authenticated_client, sample_campaign):
        """Test campaign followups endpoint."""
        response = authenticated_client.get(f'/api/campaigns/{sample_campaign.id}/followups')
        assert response.status_code == 200
        data = response.json()
        assert 'total_threads' in data
        assert 'followups' in data
