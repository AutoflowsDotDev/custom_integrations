"""Tests for the ai_processor module."""
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

from src.ai_service.ai_processor import AIProcessor
from src.core.types import EmailData


@pytest.fixture
def mock_pipeline():
    """Create a mock transformers pipeline."""
    pipeline_mock = MagicMock()
    
    # Configure sentiment analysis (urgency) output
    pipeline_mock.return_value.side_effect = None
    pipeline_mock.return_value.return_value = [
        {"label": "POSITIVE", "score": 0.95}  # High confidence positive sentiment
    ]
    
    return pipeline_mock


@pytest.fixture
def mock_summarization_pipeline():
    """Create a mock transformers summarization pipeline."""
    pipeline_mock = MagicMock()
    pipeline_mock.return_value.return_value = [
        {"summary_text": "This is a summarized text of the email content."}
    ]
    return pipeline_mock


class TestAIProcessor:
    """Tests for the AIProcessor class."""

    @patch('src.ai_service.ai_processor.pipeline')
    def test_init_successful(self, mock_pipeline_func):
        """Test successful initialization of AIProcessor."""
        # Arrange
        urgency_pipeline_mock = MagicMock()
        summarization_pipeline_mock = MagicMock()
        
        # Configure pipeline to return different instances based on task
        def pipeline_side_effect(task, model):
            if task == "sentiment-analysis":
                return urgency_pipeline_mock
            elif task == "summarization":
                return summarization_pipeline_mock
            return None
        
        mock_pipeline_func.side_effect = pipeline_side_effect
        
        # Act
        ai_processor = AIProcessor()
        
        # Assert
        assert ai_processor.urgency_pipeline == urgency_pipeline_mock
        assert ai_processor.summarization_pipeline == summarization_pipeline_mock
        
        # Check that pipeline was called with expected arguments
        assert mock_pipeline_func.call_count == 2
        mock_pipeline_func.assert_any_call("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        mock_pipeline_func.assert_any_call("summarization", model="facebook/bart-large-cnn")

    @patch('src.ai_service.ai_processor.pipeline')
    def test_init_handles_pipeline_exceptions(self, mock_pipeline_func):
        """Test handling of exceptions during pipeline initialization."""
        # Arrange
        # Fail only on urgency pipeline
        def pipeline_side_effect(task, model):
            if task == "sentiment-analysis":
                raise Exception("Failed to load urgency model")
            return MagicMock()
        
        mock_pipeline_func.side_effect = pipeline_side_effect
        
        # Act
        with patch('src.ai_service.ai_processor.logger.error') as mock_error:
            ai_processor = AIProcessor()
            
            # Assert
            assert ai_processor.urgency_pipeline is None
            assert ai_processor.summarization_pipeline is not None
            mock_error.assert_called_once()
            assert "Failed to load urgency" in mock_error.call_args[0][0]

    @patch('src.ai_service.ai_processor.pipeline')
    def test_get_text_for_analysis(self, mock_pipeline_func, mock_email_data):
        """Test extraction of text for analysis."""
        # Arrange
        mock_pipeline_func.return_value = MagicMock()
        ai_processor = AIProcessor()
        
        # Act
        result = ai_processor._get_text_for_analysis(mock_email_data)
        
        # Assert
        assert result.startswith("Subject: Test Subject")
        assert "This is a test email body." in result

    @patch('src.ai_service.ai_processor.pipeline')
    def test_get_text_for_analysis_handles_empty_fields(self, mock_pipeline_func):
        """Test text extraction handles empty fields."""
        # Arrange
        mock_pipeline_func.return_value = MagicMock()
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

    @patch('src.ai_service.ai_processor.pipeline')
    def test_analyze_urgency_positive(self, mock_pipeline_func):
        """Test urgency analysis with positive result."""
        # Arrange - Configure mock pipeline
        urgency_pipeline = MagicMock()
        urgency_pipeline.return_value = [{"label": "POSITIVE", "score": 0.95}]
        
        mock_pipeline_func.side_effect = lambda task, model: urgency_pipeline if task == "sentiment-analysis" else MagicMock()
        
        ai_processor = AIProcessor()
        
        # Act
        result = ai_processor.analyze_urgency("This is an URGENT email that requires immediate attention!")
        
        # Assert
        assert result["is_urgent"] is True
        assert result["confidence_score"] == 0.95

    @patch('src.ai_service.ai_processor.pipeline')
    def test_analyze_urgency_negative(self, mock_pipeline_func):
        """Test urgency analysis with negative result."""
        # Arrange - Configure mock pipeline
        urgency_pipeline = MagicMock()
        urgency_pipeline.return_value = [{"label": "NEGATIVE", "score": 0.85}]
        
        mock_pipeline_func.side_effect = lambda task, model: urgency_pipeline if task == "sentiment-analysis" else MagicMock()
        
        ai_processor = AIProcessor()
        
        # Act
        result = ai_processor.analyze_urgency("This is a regular update email.")
        
        # Assert
        assert result["is_urgent"] is False
        assert result["confidence_score"] == 0.85

    @patch('src.ai_service.ai_processor.pipeline')
    def test_analyze_urgency_keyword_detection(self, mock_pipeline_func):
        """Test urgency detection using keywords."""
        # Arrange - Configure mock pipeline to return non-urgent by sentiment
        urgency_pipeline = MagicMock()
        urgency_pipeline.return_value = [{"label": "NEGATIVE", "score": 0.75}]
        
        mock_pipeline_func.side_effect = lambda task, model: urgency_pipeline if task == "sentiment-analysis" else MagicMock()
        
        ai_processor = AIProcessor()
        
        # Act - Use keyword that should trigger urgency
        result = ai_processor.analyze_urgency("Please respond asap to this inquiry.")
        
        # Assert - Should be flagged as urgent due to 'asap' keyword despite negative sentiment
        assert result["is_urgent"] is True

    @patch('src.ai_service.ai_processor.pipeline')
    def test_analyze_urgency_exception(self, mock_pipeline_func):
        """Test error handling during urgency analysis."""
        # Arrange - Configure pipeline to throw exception
        urgency_pipeline = MagicMock()
        urgency_pipeline.side_effect = Exception("Model failed")
        
        mock_pipeline_func.side_effect = lambda task, model: urgency_pipeline if task == "sentiment-analysis" else MagicMock()
        
        ai_processor = AIProcessor()
        
        # Act
        with patch('src.ai_service.ai_processor.logger.error') as mock_error:
            result = ai_processor.analyze_urgency("Test email content")
            
            # Assert
            assert result["is_urgent"] is False
            assert result["confidence_score"] is None
            mock_error.assert_called_once()
            assert "Error during urgency analysis" in mock_error.call_args[0][0]

    @patch('src.ai_service.ai_processor.pipeline')
    def test_summarize_email(self, mock_pipeline_func):
        """Test email summarization."""
        # Arrange
        summary_pipeline = MagicMock()
        summary_pipeline.return_value = [{"summary_text": "This is the summarized email."}]
        
        mock_pipeline_func.side_effect = lambda task, model: summary_pipeline if task == "summarization" else MagicMock()
        
        ai_processor = AIProcessor()
        
        # Act
        result = ai_processor.summarize_email("This is a long email with lots of content that needs to be summarized. It contains multiple sentences with important information.")
        
        # Assert
        assert result["summary"] == "This is the summarized email."

    @patch('src.ai_service.ai_processor.pipeline')
    def test_summarize_short_email(self, mock_pipeline_func):
        """Test summarization handling of short emails."""
        # Arrange
        summary_pipeline = MagicMock()
        # This should not be called for short emails
        
        mock_pipeline_func.side_effect = lambda task, model: summary_pipeline if task == "summarization" else MagicMock()
        
        ai_processor = AIProcessor()
        short_text = "Short email."
        
        # Act
        result = ai_processor.summarize_email(short_text)
        
        # Assert
        # Should return original text, not attempt to summarize
        assert result["summary"] == short_text
        # Pipeline should not be called for short text
        summary_pipeline.assert_not_called()

    @patch('src.ai_service.ai_processor.pipeline')
    def test_summarize_email_exception(self, mock_pipeline_func):
        """Test error handling during summarization."""
        # Arrange
        summary_pipeline = MagicMock()
        summary_pipeline.side_effect = Exception("Summarization failed")
        
        mock_pipeline_func.side_effect = lambda task, model: summary_pipeline if task == "summarization" else MagicMock()
        
        ai_processor = AIProcessor()
        
        # Act
        # Make a longer text to avoid the short-text condition
        long_text = "This is a longer email " * 20 + "that should be summarized but will fail due to an exception."
        
        with patch('src.ai_service.ai_processor.logger.error') as mock_error:
            result = ai_processor.summarize_email(long_text)
            
            # Assert
            assert "Error during email summarization" in mock_error.call_args[0][0]
            assert result["summary"] == long_text  # It should return the original text on error

    @patch('src.ai_service.ai_processor.pipeline')
    def test_process_email_urgent(self, mock_pipeline_func, mock_urgent_email_data):
        """Test processing an urgent email."""
        # Arrange - Configure mock pipeline
        urgency_pipeline = MagicMock()
        urgency_pipeline.return_value = [{"label": "POSITIVE", "score": 0.95}]
        
        summary_pipeline = MagicMock()
        summary_pipeline.return_value = [{"summary_text": "Urgent matter requiring attention."}]
        
        def pipeline_side_effect(task, model):
            if task == "sentiment-analysis":
                return urgency_pipeline
            elif task == "summarization":
                return summary_pipeline
            return None
        
        mock_pipeline_func.side_effect = pipeline_side_effect
        
        ai_processor = AIProcessor()
        
        # Patch methods to isolate behavior
        with patch.object(ai_processor, '_get_text_for_analysis', return_value="Urgent test content"), \
             patch.object(ai_processor, '_get_text_for_summarization', return_value="Content to summarize"):
            
            # Act
            result = ai_processor.process_email(mock_urgent_email_data)
            
            # Assert
            assert result["is_urgent"] is True
            # summary_pipeline.return_value would be used, which returns "Urgent matter requiring attention."
            assert result["summary"] == "Urgent matter requiring attention."
            # Original email data fields should be preserved
            assert result["id"] == mock_urgent_email_data["id"]
            assert result["subject"] == mock_urgent_email_data["subject"]

    @patch('src.ai_service.ai_processor.pipeline')
    def test_process_email_not_urgent(self, mock_pipeline_func, mock_email_data):
        """Test processing a non-urgent email."""
        # Arrange
        urgency_pipeline = MagicMock()
        urgency_pipeline.return_value = [{"label": "NEGATIVE", "score": 0.85}]
        
        summary_pipeline = MagicMock()
        # This should not be called for non-urgent emails in our current design
        
        def pipeline_side_effect(task, model):
            if task == "sentiment-analysis":
                return urgency_pipeline
            elif task == "summarization":
                return summary_pipeline
            return None
        
        mock_pipeline_func.side_effect = pipeline_side_effect
        
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