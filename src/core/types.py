from typing import TypedDict, List, Optional
from datetime import datetime

class EmailData(TypedDict):
    id: str
    thread_id: str # Added thread_id for context
    subject: Optional[str]
    sender: Optional[str]
    body_plain: Optional[str]
    body_html: Optional[str]
    received_timestamp: datetime
    snippet: Optional[str]

class AnalyzedEmailData(EmailData):
    is_urgent: bool
    summary: Optional[str]

class SlackMessage(TypedDict):
    channel: str
    text: str
    # Add other Slack message fields if needed, like blocks for rich formatting
    # blocks: Optional[List[dict]]

# Example of a more complex type if needed for AI models
class AITaskInput(TypedDict):
    email_content: str
    # other relevant fields

class UrgencyResponse(TypedDict):
    is_urgent: bool
    confidence_score: Optional[float]
    # other details

class SummarizationResponse(TypedDict):
    summary: str
    # other details 