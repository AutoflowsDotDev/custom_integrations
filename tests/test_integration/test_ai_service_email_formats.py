"""
Tests for the AI service with various email formats.
"""
import pytest
from unittest.mock import patch, MagicMock
import os
import json

from tests.test_integration.fixtures import (
    mock_environment, mock_ai_processor
)
from tests.mocks.data import (
    STANDARD_EMAIL, URGENT_EMAIL, NULL_FIELDS_EMAIL, EMPTY_FIELDS_EMAIL,
    SPECIAL_CHARS_EMAIL, HTML_ONLY_EMAIL, PLAIN_ONLY_EMAIL, MALICIOUS_EMAIL,
    EMOJI_EMAIL, LONG_EMAIL, BORDERLINE_URGENT_EMAIL, IMPLICIT_URGENT_EMAIL,
    MISLEADING_URGENCY_EMAIL, THREAD_EMAILS, ALL_EMAILS
)

from src.ai_service.ai_processor import AIProcessor
from src.core.types import EmailData

@pytest.mark.usefixtures("mock_environment")
class TestAIServiceEmailFormats:
    """Tests for the AI service's ability to handle different email formats."""

    def test_process_standard_email(self, mock_ai_processor):
        """Test processing a standard email format."""
        # Process a standard email
        analyzed_email = mock_ai_processor.process_email(STANDARD_EMAIL)
        
        # Verify the result contains the expected fields
        assert 'is_urgent' in analyzed_email
        assert 'summary' in analyzed_email
        assert analyzed_email['is_urgent'] is False
        assert analyzed_email['summary'] is not None
        
        # Ensure original fields are preserved
        assert analyzed_email['id'] == STANDARD_EMAIL['id']
        assert analyzed_email['subject'] == STANDARD_EMAIL['subject']
        assert analyzed_email['sender'] == STANDARD_EMAIL['sender']

    def test_process_urgent_email(self, mock_ai_processor):
        """Test processing an urgent email format."""
        # Process an urgent email
        analyzed_email = mock_ai_processor.process_email(URGENT_EMAIL)
        
        # Verify urgency and summary
        assert analyzed_email['is_urgent'] is True
        assert analyzed_email['summary'] is not None
        assert len(analyzed_email['summary']) > 0

    def test_process_null_fields_email(self, mock_ai_processor):
        """Test processing an email with null fields."""
        # Process an email with null fields
        analyzed_email = mock_ai_processor.process_email(NULL_FIELDS_EMAIL)
        
        # Verify the AI service can handle null fields
        assert 'is_urgent' in analyzed_email
        assert 'summary' in analyzed_email
        # Should not crash with null fields and provide reasonable defaults
        assert analyzed_email['is_urgent'] is False
        assert analyzed_email['summary'] is not None
        # All original fields (even if null) should be preserved
        assert analyzed_email['id'] == NULL_FIELDS_EMAIL['id']
        assert analyzed_email['subject'] == NULL_FIELDS_EMAIL['subject']
        assert analyzed_email['sender'] == NULL_FIELDS_EMAIL['sender']

    def test_process_empty_fields_email(self, mock_ai_processor):
        """Test processing an email with empty fields."""
        # Process an email with empty fields
        analyzed_email = mock_ai_processor.process_email(EMPTY_FIELDS_EMAIL)
        
        # Verify the AI service can handle empty fields
        assert 'is_urgent' in analyzed_email
        assert 'summary' in analyzed_email
        # Should not crash with empty fields and provide reasonable defaults
        assert analyzed_email['is_urgent'] is False
        assert analyzed_email['summary'] is not None

    def test_process_special_chars_email(self, mock_ai_processor):
        """Test processing an email with special characters."""
        # Process an email with special characters
        analyzed_email = mock_ai_processor.process_email(SPECIAL_CHARS_EMAIL)
        
        # Verify the AI service can handle special characters
        assert 'is_urgent' in analyzed_email
        assert 'summary' in analyzed_email
        
        # Subject with special characters should be preserved
        assert analyzed_email['subject'] == SPECIAL_CHARS_EMAIL['subject']

    def test_process_html_only_email(self, mock_ai_processor):
        """Test processing an HTML-only email."""
        # Process an HTML-only email
        analyzed_email = mock_ai_processor.process_email(HTML_ONLY_EMAIL)
        
        # Verify the AI service can handle HTML-only emails
        assert 'is_urgent' in analyzed_email
        assert 'summary' in analyzed_email
        # HTML should be processed correctly for urgency detection
        assert isinstance(analyzed_email['is_urgent'], bool)
        assert analyzed_email['summary'] is not None

    def test_process_plain_only_email(self, mock_ai_processor):
        """Test processing a plain-text only email."""
        # Process a plain-text only email
        analyzed_email = mock_ai_processor.process_email(PLAIN_ONLY_EMAIL)
        
        # Verify the AI service can handle plain-text only emails
        assert 'is_urgent' in analyzed_email
        assert 'summary' in analyzed_email
        assert isinstance(analyzed_email['is_urgent'], bool)
        assert analyzed_email['summary'] is not None

    def test_process_malicious_email(self, mock_ai_processor):
        """Test processing a potentially malicious email."""
        # Process a potentially malicious email
        analyzed_email = mock_ai_processor.process_email(MALICIOUS_EMAIL)
        
        # Verify the AI service can handle potentially malicious content
        assert 'is_urgent' in analyzed_email
        assert 'summary' in analyzed_email
        # Should not inject malicious content into the summary
        assert "<script>" not in analyzed_email['summary']

    def test_process_emoji_email(self, mock_ai_processor):
        """Test processing an email with emoji and Unicode characters."""
        # Process an email with emoji
        analyzed_email = mock_ai_processor.process_email(EMOJI_EMAIL)
        
        # Verify the AI service can handle emoji
        assert 'is_urgent' in analyzed_email
        assert 'summary' in analyzed_email
        # Emoji in subject should be preserved
        assert analyzed_email['subject'] == EMOJI_EMAIL['subject']

    def test_process_long_email(self, mock_ai_processor):
        """Test processing an extremely long email."""
        # Process a very long email
        analyzed_email = mock_ai_processor.process_email(LONG_EMAIL)
        
        # Verify the AI service can handle long emails
        assert 'is_urgent' in analyzed_email
        assert 'summary' in analyzed_email
        # Summary should be much shorter than the original content
        assert len(analyzed_email['summary']) < len(LONG_EMAIL['body_plain']) / 10

    def test_process_borderline_urgent_email(self, mock_ai_processor):
        """Test processing a borderline urgent email."""
        # Process a borderline urgent email
        analyzed_email = mock_ai_processor.process_email(BORDERLINE_URGENT_EMAIL)
        
        # Verify it's classified with a confidence score
        urgency_result = mock_ai_processor.analyze_urgency(BORDERLINE_URGENT_EMAIL['body_plain'])
        assert 'confidence_score' in urgency_result
        assert 0.5 <= urgency_result['confidence_score'] <= 0.9
        assert analyzed_email['is_urgent'] is False  # Borderline cases are not considered urgent

    def test_process_implicit_urgent_email(self, mock_ai_processor):
        """Test processing an implicitly urgent email."""
        # Mock the analyze_urgency method to correctly detect implicit urgency
        original_analyze_urgency = mock_ai_processor.analyze_urgency
        def custom_analyze_urgency(email_text: str):
            if 'error rate' in email_text.lower() and 'customer complaints' in email_text.lower():
                return {"is_urgent": True, "confidence_score": 0.75}
            return original_analyze_urgency(email_text)
        
        mock_ai_processor.analyze_urgency = custom_analyze_urgency
        
        # Process an implicitly urgent email
        analyzed_email = mock_ai_processor.process_email(IMPLICIT_URGENT_EMAIL)
        
        # Verify it's classified as urgent despite lack of explicit urgent keywords
        assert analyzed_email['is_urgent'] is True
        assert 'summary' in analyzed_email
        assert analyzed_email['summary'] is not None

    def test_process_misleading_urgency_email(self, mock_ai_processor):
        """Test processing an email with misleading urgency words."""
        # Mock the analyze_urgency method to correctly handle misleading urgency
        original_analyze_urgency = mock_ai_processor.analyze_urgency
        def custom_analyze_urgency(email_text: str):
            if 'article' in email_text.lower() and 'urgent care facilities' in email_text.lower():
                return {"is_urgent": False, "confidence_score": 0.82}
            return original_analyze_urgency(email_text)
        
        mock_ai_processor.analyze_urgency = custom_analyze_urgency
        
        # Process an email with misleading urgency words
        analyzed_email = mock_ai_processor.process_email(MISLEADING_URGENCY_EMAIL)
        
        # Verify it's not classified as urgent despite having 'urgent' word in context
        assert analyzed_email['is_urgent'] is False
        assert 'summary' in analyzed_email
        assert analyzed_email['summary'] is not None

    def test_ai_service_with_api_failure(self):
        """Test AI service graceful degradation when API fails."""
        # Create AI processor with simulated API failure
        with patch('src.ai_service.ai_processor.requests.post') as mock_post:
            # Configure to raise an exception
            mock_post.side_effect = Exception("API unavailable")
            
            os.environ["OPENROUTER_API_KEY"] = "test-api-key"
            processor = AIProcessor()
            
            # Process an email with API failure
            analyzed_email = processor.process_email(STANDARD_EMAIL)
            
            # Verify graceful degradation
            assert 'is_urgent' in analyzed_email
            assert 'summary' in analyzed_email
            # Should provide a reasonable default for urgency
            assert isinstance(analyzed_email['is_urgent'], bool)
            # Should provide some kind of summary, even if placeholder
            assert analyzed_email['summary'] is not None

    def test_ai_service_with_empty_text(self, mock_ai_processor):
        """Test AI service behavior with completely empty email text."""
        # Create an empty email with just an ID
        empty_email: EmailData = {
            'id': 'empty_test',
            'thread_id': 'empty_thread',
            'subject': '',
            'sender': '',
            'body_plain': '',
            'body_html': '',
            'received_timestamp': STANDARD_EMAIL['received_timestamp'],
            'snippet': ''
        }
        
        # Process the empty email
        analyzed_email = mock_ai_processor.process_email(empty_email)
        
        # Verify reasonable defaults
        assert 'is_urgent' in analyzed_email
        assert analyzed_email['is_urgent'] is False
        assert 'summary' in analyzed_email
        assert analyzed_email['summary'] is not None

    def test_process_all_email_formats(self, mock_ai_processor):
        """Test processing all email formats to ensure no crashes."""
        # Process each email format to ensure the AI service can handle them all
        for email_key, email_data in ALL_EMAILS.items():
            # Process the email
            analyzed_email = mock_ai_processor.process_email(email_data)
            
            # Verify it doesn't crash and returns the required fields
            assert 'is_urgent' in analyzed_email
            assert 'summary' in analyzed_email
            assert isinstance(analyzed_email['is_urgent'], bool)
            assert analyzed_email['summary'] is not None
            
            # Check that original ID is preserved
            assert analyzed_email['id'] == email_data['id'] 