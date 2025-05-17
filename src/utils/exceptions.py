"""
Custom exception types for the Email Triage Application.

This module defines custom exceptions that provide more specific error information
for different components of the application, improving error handling and debugging.
"""

# Base exception class for all application-specific exceptions
class EmailTriageError(Exception):
    """Base exception class for all application-specific exceptions."""
    pass

# Configuration-related exceptions
class ConfigError(EmailTriageError):
    """Exception raised for configuration errors."""
    pass

# Gmail Service Exceptions
class GmailServiceError(EmailTriageError):
    """Base exception for Gmail service errors."""
    pass

class GmailAuthenticationError(GmailServiceError):
    """Exception raised for Gmail authentication errors."""
    pass

class GmailAPIError(GmailServiceError):
    """Exception raised for Gmail API errors."""
    pass

class MessageProcessingError(GmailServiceError):
    """Exception raised when processing an email message fails."""
    pass

# Pub/Sub Exceptions
class PubSubError(EmailTriageError):
    """Base exception for Google Cloud Pub/Sub errors."""
    pass

class PubSubConnectionError(PubSubError):
    """Exception raised for Pub/Sub connection errors."""
    pass

class PubSubMessageError(PubSubError):
    """Exception raised for errors processing Pub/Sub messages."""
    pass

# Slack Service Exceptions
class SlackServiceError(EmailTriageError):
    """Base exception for Slack service errors."""
    pass

class SlackAuthenticationError(SlackServiceError):
    """Exception raised for Slack authentication errors."""
    pass

class SlackMessageDeliveryError(SlackServiceError):
    """Exception raised when a Slack message fails to be delivered."""
    pass

# AI Service Exceptions
class AIServiceError(EmailTriageError):
    """Base exception for AI service errors."""
    pass

class ModelLoadError(AIServiceError):
    """Exception raised when an AI model fails to load."""
    pass

class UrgencyAnalysisError(AIServiceError):
    """Exception raised when urgency analysis fails."""
    pass

class SummarizationError(AIServiceError):
    """Exception raised when email summarization fails."""
    pass

# Application Logic Exceptions
class ApplicationError(EmailTriageError):
    """Base exception for application logic errors."""
    pass

class EmailProcessingError(ApplicationError):
    """Exception raised when the email processing pipeline fails."""
    pass

class IntegrationError(ApplicationError):
    """Exception raised when integration between services fails."""
    pass

# Data Validation Exceptions
class ValidationError(EmailTriageError):
    """Exception raised for data validation errors."""
    pass

class InvalidEmailFormatError(ValidationError):
    """Exception raised when email data doesn't meet expected format."""
    pass 