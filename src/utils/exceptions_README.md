# Custom Exceptions

This document explains how to use the custom exception types defined in `src/utils/exceptions.py`.

## Overview

Custom exceptions provide several benefits:
- More specific error information for debugging
- Ability to catch and handle specific error types
- Better documentation of possible failure modes
- Improved error messages for users and developers

## Exception Hierarchy

```
EmailTriageError (base class)
├── ConfigError
├── GmailServiceError
│   ├── GmailAuthenticationError
│   ├── GmailAPIError
│   └── MessageProcessingError
├── PubSubError
│   ├── PubSubConnectionError
│   └── PubSubMessageError
├── SlackServiceError
│   ├── SlackAuthenticationError
│   └── SlackMessageDeliveryError
├── AIServiceError
│   ├── ModelLoadError
│   ├── UrgencyAnalysisError
│   └── SummarizationError
├── ApplicationError
│   ├── EmailProcessingError
│   └── IntegrationError
└── ValidationError
    └── InvalidEmailFormatError
```

## Usage Examples

### Raising Custom Exceptions

```python
from src.utils.exceptions import GmailAuthenticationError, SlackMessageDeliveryError

# In Gmail service code
if not credentials:
    raise GmailAuthenticationError("Failed to authenticate with Gmail API: credentials not found")

# In Slack service code
if response.status_code != 200:
    raise SlackMessageDeliveryError(f"Failed to deliver message: {response.error}")
```

### Handling Custom Exceptions

```python
from src.utils.exceptions import (
    GmailServiceError,
    SlackServiceError,
    AIServiceError,
    EmailTriageError
)

try:
    # Process email and send notification
    process_email(email_data)
except GmailServiceError as e:
    logger.error(f"Gmail service error: {e}")
    # Handle Gmail-specific error (retry, notify admin, etc.)
except SlackServiceError as e:
    logger.error(f"Slack service error: {e}")
    # Handle Slack-specific error
except AIServiceError as e:
    logger.error(f"AI service error: {e}")
    # Handle AI-specific error (fall back to rule-based classification)
except EmailTriageError as e:
    # Catch any other application-specific error
    logger.error(f"Email triage error: {e}")
except Exception as e:
    # Catch any other unexpected error
    logger.critical(f"Unexpected error: {e}", exc_info=True)
```

## Adding New Exception Types

When adding new exception types:

1. Identify the service or component the exception belongs to
2. Choose the appropriate parent class from the hierarchy
3. Add a descriptive docstring explaining when this exception is raised
4. Include in the import statement when used in other modules

Example:
```python
class NewServiceError(EmailTriageError):
    """Base exception for new service errors."""
    pass

class SpecificNewServiceError(NewServiceError):
    """Exception raised when a specific error occurs in the new service."""
    pass
``` 