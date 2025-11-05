"""
Integration tests for end-to-end workflows.
"""
import pytest
import json
from coreapp.models import Lead, Campaign, Thread, ThreadMessage


class TestLeadNurturingWorkflow:
    """Test complete lead nurturing workflow."""

    def test_complete_campaign_workflow(self, authenticated_client, sample_leads):
        """Test end-to-end campaign creation and management."""
        # Step 1: Create campaign
        create_response = authenticated_client.post(
            '/api/campaigns',
            data=json.dumps({
                'name': 'Integration Test Campaign',
                'project': 'Beachgate by Address',
                'channel': 'email',
                'offer_text': '5% discount',
                'lead_ids': [sample_leads[0].id]
            }),
            content_type='application/json'
        )
        assert create_response.status_code == 200
        campaign_data = create_response.json()
        campaign_id = campaign_data['campaign_id']
        assert campaign_data['sent_count'] == 1

        # Step 2: Simulate lead reply
        reply_response = authenticated_client.post(
            f'/api/campaigns/{campaign_id}/lead/{sample_leads[0].id}/reply',
            data=json.dumps({
                'message': 'What amenities are available?'
            }),
            content_type='application/json'
        )
        assert reply_response.status_code == 200
        reply_data = reply_response.json()
        assert 'agent_response' in reply_data
        assert 'thread_id' in reply_data

        # Step 3: Check metrics
        metrics_response = authenticated_client.get(f'/api/campaigns/{campaign_id}/metrics')
        assert metrics_response.status_code == 200
        metrics_data = metrics_response.json()
        assert metrics_data['messages_sent'] == 1
        assert metrics_data['unique_leads_responded'] >= 1

        # Step 4: Check followups
        followups_response = authenticated_client.get(f'/api/campaigns/{campaign_id}/followups')
        assert followups_response.status_code == 200
        followups_data = followups_response.json()
        assert followups_data['total_threads'] >= 1


class TestAgentRoutingWorkflow:
    """Test agent routing decisions."""

    def test_agent_routes_correctly(self, authenticated_client, sample_leads):
        """Test agent correctly routes different query types."""
        test_cases = [
            {
                'question': 'What are the amenities at Beachgate?',
                'expected_route': 'rag',
                'should_have': ['answer', 'sources']
            },
            {
                'question': 'Count all Connected leads',
                'expected_route': 't2sql',
                'should_have': ['sql', 'rows']
            }
        ]

        for test_case in test_cases:
            response = authenticated_client.post(
                '/api/agent/query',
                data=json.dumps({'question': test_case['question']}),
                content_type='application/json'
            )
            assert response.status_code == 200
            data = response.json()
            assert data['route'] == test_case['expected_route']

            for field in test_case['should_have']:
                assert field in data


class TestDocumentIngestionWorkflow:
    """Test document upload and retrieval workflow."""

    def test_document_search_after_ingestion(self, authenticated_client):
        """Test searching documents returns results."""
        # Search for existing documents
        response = authenticated_client.get('/api/docs/search?q=amenities&k=2')
        assert response.status_code == 200
        data = response.json()
        assert 'matches' in data
        matches = data['matches']

        # Verify each match has required fields
        for match in matches:
            assert 'text' in match or 'metadata' in match


class TestT2SQLWorkflow:
    """Test Text-to-SQL generation and execution."""

    def test_t2sql_generates_valid_sql(self, authenticated_client, sample_leads):
        """Test T2SQL generates and executes valid SQL."""
        questions = [
            'How many leads are there?',
            'Count leads by status',
            'List all Connected leads'
        ]

        for question in questions:
            response = authenticated_client.post(
                '/api/t2sql/query',
                data=json.dumps({'question': question}),
                content_type='application/json'
            )
            assert response.status_code == 200
            data = response.json()

            # Verify SQL was generated
            assert 'sql' in data
            assert data['sql'] is not None
            assert 'SELECT' in data['sql'].upper()

            # Verify query was executed
            assert 'rows' in data
            assert isinstance(data['rows'], list)


class TestConversationContinuity:
    """Test conversation history and context tracking."""

    def test_conversation_history_maintained(self, authenticated_client):
        """Test agent maintains conversation history."""
        # First query
        response1 = authenticated_client.post(
            '/api/agent/query',
            data=json.dumps({'question': 'What properties are available?'}),
            content_type='application/json'
        )
        assert response1.status_code == 200
        data1 = response1.json()
        thread_id = data1['thread_id']

        # Follow-up query with same thread_id
        response2 = authenticated_client.post(
            '/api/agent/query',
            data=json.dumps({
                'question': 'Tell me more about the first one',
                'thread_id': thread_id
            }),
            content_type='application/json'
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2['thread_id'] == thread_id
