from typing import Optional, Tuple
from transformers import pipeline, Pipeline
from src.core.types import EmailData, UrgencyResponse, SummarizationResponse, AnalyzedEmailData
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Recommended: Specify model names explicitly. Fine-tune for better performance.
# For urgency, a text classification model fine-tuned on urgent/non-urgent emails.
# For summarization, a model like BART, T5, or Pegasus.
DEFAULT_URGENCY_MODEL = "distilbert-base-uncased-finetuned-sst-2-english" # Example, replace with a suitable model
DEFAULT_SUMMARIZATION_MODEL = "facebook/bart-large-cnn" # Example summarization model

class AIProcessor:
    """Handles AI-based email processing: urgency detection and summarization."""

    def __init__(self, 
                 urgency_model_name: str = DEFAULT_URGENCY_MODEL, 
                 summarization_model_name: str = DEFAULT_SUMMARIZATION_MODEL) -> None:
        try:
            logger.info(f"Loading urgency detection model: {urgency_model_name}")
            # For urgency, you might need a specific label mapping if the model is multi-class
            # This example uses a sentiment model, adapt for actual urgency classification
            self.urgency_pipeline: Optional[Pipeline] = pipeline("sentiment-analysis", model=urgency_model_name)
            logger.info("Urgency detection model loaded.")
        except Exception as e:
            logger.error(f"Failed to load urgency detection model '{urgency_model_name}': {e}")
            logger.warning("Urgency detection will be non-functional.")
            self.urgency_pipeline = None

        try:
            logger.info(f"Loading summarization model: {summarization_model_name}")
            self.summarization_pipeline: Optional[Pipeline] = pipeline("summarization", model=summarization_model_name)
            logger.info("Summarization model loaded.")
        except Exception as e:
            logger.error(f"Failed to load summarization model '{summarization_model_name}': {e}")
            logger.warning("Summarization will be non-functional.")
            self.summarization_pipeline = None

    def _get_text_for_analysis(self, email_data: EmailData) -> str:
        """Extracts and combines relevant text from email for AI analysis."""
        subject = email_data.get('subject', '') or ''
        body = email_data.get('body_plain', '') or ''
        # snippet = email_data.get('snippet', '') or '' # Snippet might be too short or redundant
        
        # Combine subject and body for a more comprehensive analysis
        # Prioritize plain text body, fallback to subject if body is empty.
        # Consider a max length for processing to avoid issues with very long emails.
        combined_text = f"Subject: {subject}\n\nBody: {body}".strip()
        
        # Limit length to avoid overly long inputs to models (e.g., first 1000-2000 chars)
        # This limit depends on the model's max input token length.
        # For BERT-like models, it's often 512 tokens. For summarization, it can be more.
        max_len_for_urgency = 1024 # Characters, roughly translates to tokens
        return combined_text[:max_len_for_urgency] if combined_text else ""
    
    def _get_text_for_summarization(self, email_data: EmailData) -> str:
        """Extracts text specifically for summarization."""
        body = email_data.get('body_plain', '') or ''
        if not body:
            subject = email_data.get('subject', '') or ''
            logger.info("No plain text body found for summarization, using subject.")
            return subject[:1024] # Max length for subject summarization
        
        # BART typically handles up to 1024 tokens. Adjust max_length as per model.
        # For very long emails, consider chunking or selecting most relevant parts.
        return body[:4096] # Limit length for summarization input

    def analyze_urgency(self, email_text: str) -> UrgencyResponse:
        """Detects the urgency of an email."""
        if not self.urgency_pipeline or not email_text:
            logger.warning("Urgency pipeline not available or no text to analyze. Defaulting to not urgent.")
            return {'is_urgent': False, 'confidence_score': None}
        
        try:
            # This is a placeholder. A real urgency model would be trained for 'URGENT'/'NOT_URGENT' labels.
            # The example model (distilbert-base-uncased-finetuned-sst-2-english) is for sentiment (POSITIVE/NEGATIVE).
            # We'll map POSITIVE sentiment to urgent for this example, which is NOT a reliable urgency indicator.
            # Replace with actual urgency classification logic.
            result = self.urgency_pipeline(email_text)
            logger.debug(f"Urgency analysis result: {result}")
            
            # Example interpretation (highly dependent on the chosen model and its output labels):
            # If model output is like [{'label': 'POSITIVE', 'score': 0.99}]
            label = result[0]['label']
            score = result[0]['score']
            
            # THIS IS A CRUDE EXAMPLE - REPLACE WITH PROPER URGENCY LOGIC
            # Consider keywords, sender reputation, dedicated urgency model, etc.
            is_urgent = (label == 'POSITIVE' and score > 0.7) or \
                 ("urgent" in email_text.lower() or "asap" in email_text.lower() or "!" in email_text[-5:])
            
            return {'is_urgent': is_urgent, 'confidence_score': score if isinstance(score, float) else None}
        except Exception as e:
            logger.error(f"Error during urgency analysis: {e}")
            return {'is_urgent': False, 'confidence_score': None}

    def summarize_email(self, email_text: str, *, force: bool = False) -> SummarizationResponse:
        """Generates a summary for the email content."""
        if not self.summarization_pipeline or not email_text:
            logger.warning("Summarization pipeline not available or no text to summarize. Returning empty summary.")
            return {'summary': "Summary not available."}
        
        try:
            # Unless ``force`` is True, avoid calling the summarisation pipeline for very
            # short inputs (heuristically fewer than 20 words) because most models will
            # either error or simply echo the input.  This behaviour is expected by the
            # unit test ``test_summarize_short_email`` which asserts that the pipeline is
            # not invoked for short text.  The caller can override this heuristic by
            # passing ``force=True`` – this is used internally when an email has been
            # classified as *urgent* and we want to generate a concise summary even for
            # succinct content.

            if not force and len(email_text.split()) < 20:
                logger.info("Email text too short for meaningful summarisation; returning original text.")
                return {'summary': email_text}

            summary_result = self.summarization_pipeline(email_text, max_length=150, min_length=30, do_sample=False)
            logger.debug(f"Summarization result: {summary_result}")
            summary_text = summary_result[0]['summary_text']
            return {'summary': summary_text}
        except Exception as e:
            logger.error(f"Error during email summarization: {e}")
            # Fall back to returning the original text (truncated if extremely long) so
            # that the caller still receives a sensible summary.
            fallback_text = email_text if len(email_text) <= 1000 else email_text[:1000] + '...'
            return {'summary': fallback_text}

    def process_email(self, email_data: EmailData) -> AnalyzedEmailData:
        """Processes a single email for urgency and summarization."""
        logger.info(f"AI Processing email ID: {email_data.get('id')}")
        
        text_for_urgency = self._get_text_for_analysis(email_data)
        urgency_result = self.analyze_urgency(text_for_urgency)
        
        summary = "No summary available."
        if urgency_result['is_urgent']:
            text_for_summary = self._get_text_for_summarization(email_data)
            summary_result = self.summarize_email(text_for_summary, force=True)
            summary = summary_result['summary']
        else:
            # Optionally, summarize non-urgent emails too, or have a shorter summary
            # For now, only summarizing urgent ones as per diagram (implicitly)
            logger.info(f"Email ID {email_data.get('id')} is not urgent. Skipping detailed summarization.")
            summary = email_data.get('snippet', 'No summary available.')[:150] # Use snippet for non-urgent

        analyzed_data: AnalyzedEmailData = {
            **email_data, # type: ignore - spread EmailData fields
            'is_urgent': urgency_result['is_urgent'],
            'summary': summary
        }
        return analyzed_data

# Example Usage:
if __name__ == '__main__':
    from datetime import datetime
    # This will download models on first run, which can take time and bandwidth.
    ai_processor = AIProcessor()

    test_urgent_email: EmailData = {
        'id': 'urgent_test1',
        'thread_id': 'thread_urgent1',
        'subject': 'URGENT: Critical Server Down - Action ASAP!',
        'sender': 'ops@example.com',
        'body_plain': 'Team, production server Alpha is down. All services impacted. Please investigate immediately. This is high priority! Call me if needed.',
        'body_html': '<p>Team, production server Alpha is down. All services impacted. Please investigate immediately. This is high priority! Call me if needed.</p>',
        'received_timestamp': datetime.now(),
        'snippet': 'Team, production server Alpha is down...'
    }

    test_normal_email: EmailData = {
        'id': 'normal_test1',
        'thread_id': 'thread_normal1',
        'subject': 'Weekly Team Sync Minutes',
        'sender': 'project.manager@example.com',
        'body_plain': 'Hi Team, attached are the minutes from our weekly sync meeting. Please review by EOD Friday. Key discussion points included project timelines and upcoming sprint planning. No urgent actions required from this summary.',
        'body_html': '<p>Hi Team, attached are the minutes from our weekly sync meeting...</p>',
        'received_timestamp': datetime.now(),
        'snippet': 'Hi Team, attached are the minutes...'
    }
    
    logger.info("\n--- Testing Urgent Email ---")
    if ai_processor.urgency_pipeline and ai_processor.summarization_pipeline:
        analyzed_urgent = ai_processor.process_email(test_urgent_email)
        print(f"Email ID: {analyzed_urgent['id']}")
        print(f"Is Urgent: {analyzed_urgent['is_urgent']}")
        print(f"Summary: {analyzed_urgent['summary']}")
    else:
        print("AI pipelines not loaded. Skipping urgent email test.")

    logger.info("\n--- Testing Normal Email ---")
    if ai_processor.urgency_pipeline:
        analyzed_normal = ai_processor.process_email(test_normal_email)
        print(f"Email ID: {analyzed_normal['id']}")
        print(f"Is Urgent: {analyzed_normal['is_urgent']}")
        print(f"Summary: {analyzed_normal['summary']}") # Will be snippet for non-urgent
    else:
        print("Urgency pipeline not loaded. Skipping normal email test.")

    # Test with empty email content
    empty_email: EmailData = {
        'id': 'empty_test1',
        'thread_id': 'thread_empty1',
        'subject': None,
        'sender': 'noone@example.com',
        'body_plain': None,
        'body_html': None,
        'received_timestamp': datetime.now(),
        'snippet': ''
    }
    logger.info("\n--- Testing Empty Email ---")
    if ai_processor.urgency_pipeline:
        analyzed_empty = ai_processor.process_email(empty_email)
        print(f"Email ID: {analyzed_empty['id']}")
        print(f"Is Urgent: {analyzed_empty['is_urgent']}")
        print(f"Summary: {analyzed_empty['summary']}")
    else:
        print("Urgency pipeline not loaded. Skipping empty email test.") 