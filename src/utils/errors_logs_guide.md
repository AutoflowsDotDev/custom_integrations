# Error Handling and Logging Guide

This document outlines the error handling and logging practices implemented in the Email Triage Application according to the requirements specified in the errors_logs.mdc file.

## Error Handling

The application implements proper error handling with custom exceptions for different components and error types.

### Exception Hierarchy

- **`EmailTriageError`**: Base exception for all application errors
  - **`ConfigError`**: Configuration-related errors
  - **`GmailServiceError`**: Gmail service errors
    - **`GmailAuthenticationError`**: Gmail authentication errors
    - **`GmailAPIError`**: Gmail API errors
    - **`MessageProcessingError`**: Email message processing errors
  - **`PubSubError`**: Pub/Sub related errors
    - **`PubSubConnectionError`**: Pub/Sub connection errors
    - **`PubSubMessageError`**: Pub/Sub message processing errors
  - **`SlackServiceError`**: Slack service errors
    - **`SlackAuthenticationError`**: Slack authentication errors
    - **`SlackMessageDeliveryError`**: Slack message delivery errors
  - **`AIServiceError`**: AI service errors
    - **`ModelLoadError`**: AI model loading errors
    - **`UrgencyAnalysisError`**: Email urgency analysis errors
    - **`SummarizationError`**: Email summarization errors
  - **`ApplicationError`**: Application logic errors
    - **`EmailProcessingError`**: Email processing pipeline errors
    - **`IntegrationError`**: Service integration errors
  - **`ValidationError`**: Data validation errors
    - **`InvalidEmailFormatError`**: Email format validation errors

### Best Practices

1. **Use specific exception types**: Always catch and raise the most specific exception type appropriate for the error.
2. **Add context**: Include useful information in exception messages.
3. **Graceful degradation**: Handle exceptions in a way that allows the application to continue functioning when possible.
4. **Log exceptions**: Always log exceptions with appropriate severity.

## Logging

The application implements comprehensive logging with multiple severity levels.

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: Confirmation that things are working
- **WARNING**: Indication of potential issues
- **ERROR**: Errors that don't terminate execution
- **CRITICAL**: Critical errors causing termination

### Logging Configuration

- **Console output**: All logs are sent to stdout for immediate visibility
- **File output**: Logs are saved to multiple files:
  - `app.log`: All logs
  - `app_debug.log`: Debug-level logs only
  - `app_error.log`: Error and critical logs only
- **Log rotation**: All log files are configured with size-based rotation

### Structured Logging

- **Contextual information**: All logs include:
  - Timestamps
  - Run number: A unique identifier for each application run
  - Step information: The current workflow step being executed
  - Request ID: A unique identifier for tracking related logs

### Usage Example

```python
from src.utils.logger import get_logger

# Get a logger instance
logger = get_logger(__name__)

# Set the current workflow step
logger.set_step("initialize_component")

# Log messages at different levels
logger.debug("Detailed debug information")
logger.info("Component initialized successfully")
logger.warning("Configuration parameter missing, using default")
logger.error("Failed to connect to external service")
logger.critical("Application cannot continue due to critical error")

# Change the step when moving to a new part of the workflow
logger.set_step("process_data")
```

## Monitoring

The application is designed to be monitored through dashboarding tools like Datadog or Grafana.

### Run Numbers

Each application execution is assigned a unique run number, which is automatically included in all log messages.

### Step Tracking

Each major step in the workflow is labeled and numbered for easy tracking.

### Log Format

Log messages follow this format:
```
LEVEL - TIMESTAMP - run: NUMBER, step:STEP-MESSAGE
```

Example:
```
INFO - Jan 12, 2024 14:45:23 - run: 245, step:1-fetching_emails - Starting to fetch emails from Gmail
```

This format allows logs to be easily grouped and analyzed by:
- Run number
- Step number and name
- Timestamp
- Log level 