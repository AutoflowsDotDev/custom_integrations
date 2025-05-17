"""Tests for the ai_processor module."""
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
import os

import pytest
import requests

from src.ai_service.ai_processor import AIProcessor
from src.core.types import EmailData


@pytest.fixture
def mock_response():
    """Create a mock requests response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"classification": "URGENT", "confidence": 0.95}'
                }
            }
        ]
    }
    response.raise_for_status = MagicMock()
    return response


@pytest.fixture
def mock_summary_response():
    """Create a mock requests summary response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "This is a summarized text of the email content."
                }
            }
        ]
    }
    response.raise_for_status = MagicMock()
    return response


@pytest.fixture
def mock_email_data():
    """Create a test email data dictionary."""
    return {
        'id': 'test123',
        'thread_id': 'thread123',
        'subject': 'Test Subject',
        'sender': 'test@example.com',
        'body_plain': 'This is a test email body.',
        'body_html': '<p>This is a test email body.</p>',
        'received_timestamp': datetime.now(),
        'snippet': 'This is a test email snippet.'
    }


@pytest.fixture
def mock_urgent_email_data():
    """Create a test urgent email data dictionary."""
    return {
        'id': 'urgent123',
        'thread_id': 'urgentthread123',
        'subject': 'URGENT: Action Required Immediately',
        'sender': 'important@example.com',
        'body_plain': 'This is an urgent email requiring immediate action. Please respond ASAP.',
        'body_html': '<p>This is an urgent email requiring immediate action. Please respond ASAP.</p>',
        'received_timestamp': datetime.now(),
        'snippet': 'This is an urgent email requiring immediate action...'
    }


class TestAIProcessor:
    """Tests for the AIProcessor class."""

    def setup_method(self):
        """Set up environment for tests."""
        os.environ["OPENROUTER_API_KEY"] = "test_api_key"

    def teardown_method(self):
        """Clean up after tests."""
        if "OPENROUTER_API_KEY" in os.environ:
            del os.environ["OPENROUTER_API_KEY"]

    def test_init_successful(self):
        """Test successful initialization of AIProcessor."""
        # Act
        ai_processor = AIProcessor()
        
        # Assert
        assert ai_processor.api_key == "test_api_key"
        assert ai_processor.urgency_model == "openai/gpt-3.5-turbo"
        assert ai_processor.summarization_model == "openai/gpt-3.5-turbo"

    def test_init_handles_missing_api_key(self):
        """Test handling of missing API key."""
        # Arrange
        if "OPENROUTER_API_KEY" in os.environ:
            del os.environ["OPENROUTER_API_KEY"]
        
        # Act
        with patch('src.ai_service.ai_processor.logger.warning') as mock_warning:
            ai_processor = AIProcessor()
            
            # Assert
            assert ai_processor.api_key is None
            mock_warning.assert_called_once()
            assert "OPENROUTER_API_KEY not found" in mock_warning.call_args[0][0]

    def test_get_text_for_analysis(self, mock_email_data):
        """Test extraction of text for analysis."""
        # Arrange
        ai_processor = AIProcessor()
        
        # Act
        result = ai_processor._get_text_for_analysis(mock_email_data)
        
        # Assert
        assert result.startswith("Subject: Test Subject")
        assert "This is a test email body." in result

    def test_get_text_for_analysis_handles_empty_fields(self):
        """Test text extraction handles empty fields."""
        # Arrange
        ai_processor = AIProcessor()
        
        # Create a test email with empty fields
        empty_email = {
            'id': 'empty123',
            'thread_id': 'thread_empty123',
            'subject': None,
            'sender': None,
            'body_plain': None,
            'body_html': None,
            'received_timestamp': datetime.now(),
            'snippet': None
        }
        
        # Act
        result = ai_processor._get_text_for_analysis(empty_email)
        
        # Assert
        assert result == "Subject: \n\nBody:"

    @patch('requests.post')
    def test_analyze_urgency_positive(self, mock_post, mock_response):
        """Test urgency analysis with positive result."""
        # Arrange - Configure mock response
        mock_post.return_value = mock_response
        
        ai_processor = AIProcessor()
        
        # Act
        result = ai_processor.analyze_urgency("This is an URGENT email that requires immediate attention!")
        
        # Assert
        assert result["is_urgent"] is True
        assert result["confidence_score"] == 0.95
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_analyze_urgency_negative(self, mock_post):
        """Test urgency analysis with negative result."""
        # Arrange - Configure mock response for non-urgent
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"classification": "NOT_URGENT", "confidence": 0.85}'
                    }
                }
            ]
        }
        response.raise_for_status = MagicMock()
        mock_post.return_value = response
        
        ai_processor = AIProcessor()
        
        # Act
        result = ai_processor.analyze_urgency("This is a regular update email.")
        
        # Assert
        assert result["is_urgent"] is False
        assert result["confidence_score"] == 0.85

    @patch('requests.post')
    def test_analyze_urgency_keyword_detection(self, mock_post):
        """Test urgency detection using keywords."""
        # Arrange - Configure mock response for non-urgent from API
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"classification": "NOT_URGENT", "confidence": 0.75}'
                    }
                }
            ]
        }
        response.raise_for_status = MagicMock()
        mock_post.return_value = response
        
        ai_processor = AIProcessor()
        
        # Act - Use keyword that should trigger urgency
        result = ai_processor.analyze_urgency("Please respond asap to this inquiry.")
        
        # Assert - Should be flagged as urgent due to 'asap' keyword despite API returning non-urgent
        assert result["is_urgent"] is True

    @patch('requests.post')
    def test_analyze_urgency_exception(self, mock_post):
        """Test error handling during urgency analysis."""
        # Arrange - Configure request to raise exception
        mock_post.side_effect = requests.RequestException("API request failed")
        
        ai_processor = AIProcessor()
        
        # Act
        with patch('src.ai_service.ai_processor.logger.error') as mock_error:
            result = ai_processor.analyze_urgency("Test email content")
            
            # Assert - Should fall back to keyword-based analysis
            assert isinstance(result["is_urgent"], bool)
            mock_error.assert_called_once()
            assert "Error during API urgency analysis" in mock_error.call_args[0][0]

    @patch('requests.post')
    def test_summarize_email(self, mock_post, mock_summary_response):
        """Test email summarization."""
        # Arrange
        mock_post.return_value = mock_summary_response
        
        ai_processor = AIProcessor()
        
        # Act
        result = ai_processor.summarize_email("This is a long email with lots of content that needs to be summarized. It contains multiple sentences with important information.")
        
        # Assert
        assert result["summary"] == "This is a summarized text of the email content."
        mock_post.assert_called_once()

    def test_summarize_short_email(self):
        """Test summarization handling of short emails."""
        # Arrange
        ai_processor = AIProcessor()
        short_text = "Short email."
        
        # Act - No need to mock API as it shouldn't be called
        result = ai_processor.summarize_email(short_text)
        
        # Assert - Should return original text, not attempt to summarize
        assert result["summary"] == short_text

    @patch('requests.post')
    def test_summarize_email_exception(self, mock_post):
        """Test error handling during summarization."""
        # Arrange - Request raises exception
        mock_post.side_effect = requests.RequestException("API request failed")
        
        ai_processor = AIProcessor()
        
        # Act - Use longer text to avoid short-text condition
        long_text = "This is a longer email " * 20 + "that should be summarized but will fail due to an exception."
        
        with patch('src.ai_service.ai_processor.logger.error') as mock_error:
            result = ai_processor.summarize_email(long_text)
            
            # Assert
            assert "Error during email summarization" in mock_error.call_args[0][0]
            # It should return the original text on error (truncated if very long)
            assert result["summary"].startswith("This is a longer email")

    @patch('requests.post')
    def test_process_email_urgent(self, mock_post, mock_urgent_email_data, mock_response, mock_summary_response):
        """Test processing an urgent email."""
        # Arrange - Configure mock responses
        mock_post.side_effect = [mock_response, mock_summary_response]
        
        ai_processor = AIProcessor()
        
        # Patch methods to isolate behavior
        with patch.object(ai_processor, '_get_text_for_analysis', return_value="Urgent test content"), \
             patch.object(ai_processor, '_get_text_for_summarization', return_value="Content to summarize"):
            
            # Act
            result = ai_processor.process_email(mock_urgent_email_data)
            
            # Assert
            assert result["is_urgent"] is True
            assert result["summary"] == "This is a summarized text of the email content."
            # Original email data fields should be preserved
            assert result["id"] == mock_urgent_email_data["id"]
            assert result["subject"] == mock_urgent_email_data["subject"]

    @patch('requests.post')
    def test_process_email_not_urgent(self, mock_post, mock_email_data):
        """Test processing a non-urgent email."""
        # Arrange - Configure mock response for non-urgent
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"classification": "NOT_URGENT", "confidence": 0.85}'
                    }
                }
            ]
        }
        response.raise_for_status = MagicMock()
        mock_post.return_value = response
        
        ai_processor = AIProcessor()
        
        # Set up a non-urgent email with a snippet
        test_email = dict(mock_email_data)
        test_email["snippet"] = "This is a test email snippet."
        
        # Act
        with patch.object(ai_processor, '_get_text_for_analysis', return_value="Non-urgent test content"):
            # Mock analyze_urgency to return non-urgent explicitly
            with patch.object(ai_processor, 'analyze_urgency', return_value={"is_urgent": False, "confidence_score": 0.85}):
                result = ai_processor.process_email(test_email)
                
                # Assert
                assert result["is_urgent"] is False
                # For non-urgent emails, the snippet is used
                assert result["summary"] == "This is a test email snippet."
                # Original email data fields should be preserved
                assert result["id"] == test_email["id"]
                assert result["subject"] == test_email["subject"] 