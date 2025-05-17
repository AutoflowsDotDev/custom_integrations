from typing import Optional, Tuple, Dict, Any
import os
import requests
from src.core.types import EmailData, UrgencyResponse, SummarizationResponse, AnalyzedEmailData
from src.utils.logger import get_logger

logger = get_logger(__name__)

# OpenRouter API configuration
DEFAULT_OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_URGENCY_MODEL = "openai/gpt-3.5-turbo"  # Default model for urgency detection
DEFAULT_SUMMARIZATION_MODEL = "openai/gpt-3.5-turbo"  # Default model for summarization

class AIProcessor:
    """Handles AI-based email processing: urgency detection and summarization using OpenRouter API."""

    def __init__(self, 
                 urgency_model_name: str = DEFAULT_URGENCY_MODEL, 
                 summarization_model_name: str = DEFAULT_SUMMARIZATION_MODEL) -> None:
        # Get API key from environment variables
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not found in environment variables. AI processing will not function.")
        
        self.api_url = os.environ.get("OPENROUTER_API_URL", DEFAULT_OPENROUTER_API_URL)
        self.urgency_model = urgency_model_name
        self.summarization_model = summarization_model_name
        
        # Log initialization
        logger.info(f"Initialized AIProcessor with OpenRouter API")
        logger.info(f"Urgency detection model: {self.urgency_model}")
        logger.info(f"Summarization model: {self.summarization_model}")

    def _make_openrouter_request(self, 
                               model: str, 
                               messages: list, 
                               temperature: float = 0.5, 
                               max_tokens: int = 500) -> Dict[str, Any]:
        """Make a request to the OpenRouter API."""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set in environment variables")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://your-site-url.com",  # Replace with your actual site URL
            "X-Title": "Custom Integrations"  # Application name
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Let the exception propagate to the caller for handling
        response = requests.post(self.api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def _get_text_for_analysis(self, email_data: EmailData) -> str:
        """Extracts and combines relevant text from email for AI analysis."""
        subject = email_data.get('subject', '') or ''
        body = email_data.get('body_plain', '') or ''
        
        # Combine subject and body for a more comprehensive analysis
        combined_text = f"Subject: {subject}\n\nBody: {body}".strip()
        
        # Limit length to avoid overly long inputs to models
        max_len_for_urgency = 4000  # Characters
        return combined_text[:max_len_for_urgency] if combined_text else ""
    
    def _get_text_for_summarization(self, email_data: EmailData) -> str:
        """Extracts text specifically for summarization."""
        body = email_data.get('body_plain', '') or ''
        if not body:
            subject = email_data.get('subject', '') or ''
            logger.info("No plain text body found for summarization, using subject.")
            return subject[:1024]
        
        return body[:6000]  # Limit length for summarization input

    def analyze_urgency(self, email_text: str) -> UrgencyResponse:
        """Detects the urgency of an email using OpenRouter API.
        
        Uses a hybrid approach:
        1. API-based classification
        2. Rule-based heuristics as fallback
        """
        if not email_text:
            logger.info("Empty e-mail text received for urgency analysis; returning not-urgent by default.")
            return {"is_urgent": False, "confidence_score": None}

        confidence_score: Optional[float] = None
        api_is_urgent: Optional[bool] = None

        # --- 1) API-based classification ----------------------------------------------------
        try:
            if self.api_key:
                # Create the prompt for urgency detection
                system_prompt = """
                You are an email urgency classifier. Analyze the email and determine if it requires urgent attention.
                Classify the email as either "URGENT" or "NOT_URGENT" and provide a confidence score between 0 and 1.
                Consider factors like explicit urgency keywords, time-sensitivity, consequences mentioned, 
                and overall tone. Respond in JSON format: {"classification": "URGENT or NOT_URGENT", "confidence": 0.0 to 1.0}
                """
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": email_text}
                ]
                
                response = self._make_openrouter_request(
                    model=self.urgency_model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=150
                )
                
                # Parse response to extract classification and confidence
                try:
                    content = response['choices'][0]['message']['content']
                    logger.debug(f"API urgency analysis response: {content}")
                    
                    # Check if the content contains a JSON response
                    import json
                    # Find JSON in the response (handling potential text before/after the JSON)
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        classification = result.get("classification", "").lower()
                        confidence_score = float(result.get("confidence", 0.5))
                        
                        if "urgent" in classification:
                            api_is_urgent = "not" not in classification
                        else:
                            api_is_urgent = classification == "urgent"
                    else:
                        # If no JSON found, use simple text analysis
                        content_lower = content.lower()
                        api_is_urgent = "urgent" in content_lower and "not urgent" not in content_lower
                        confidence_score = 0.6  # Default confidence when format isn't as expected
                        
                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    logger.warning(f"Error parsing API response for urgency: {e}")
                    # Fall back to text analysis
                    content = response['choices'][0]['message']['content'].lower()
                    api_is_urgent = "urgent" in content and "not urgent" not in content
                    confidence_score = 0.6  # Default confidence when format isn't as expected
                
        except Exception as e:
            logger.error(f"Error during API urgency analysis: {e}")
            # An exception here should not fail the whole pipeline – we'll fall back to heuristics.

        # --- 2) Rule-based heuristics -------------------------------------------------------
        keyword_hits = 0
        lowered = email_text.lower()
        URGENT_KEYWORDS = [
            "urgent", "asap", "immediately", "important", "high priority", "action required",
            "critical", "deadline", "response needed", "reply needed", "time-sensitive"
        ]

        for kw in URGENT_KEYWORDS:
            if kw in lowered:
                keyword_hits += 1

        exclamation_factor = min(lowered.count("!"), 3)  # cap influence of exclamation marks

        heuristic_score = min(1.0, (keyword_hits * 0.2) + (exclamation_factor * 0.1))
        heuristic_is_urgent = keyword_hits > 0 or heuristic_score >= 0.5

        # --- Decision logic ---------------------------------------------------------------
        if api_is_urgent is None:
            # API not available – rely on heuristic completely.
            final_is_urgent = heuristic_is_urgent
            final_confidence = heuristic_score
        else:
            # Combine both signals – NEVER let the API model *downgrade* a clear
            # heuristic hit (e.g. presence of the word "urgent" in the text).
            final_is_urgent = api_is_urgent or heuristic_is_urgent

            # Confidence is the higher of the two signals (scaled to the same
            # 0-1 range).
            final_confidence = max(confidence_score or 0.0, heuristic_score)

        return {"is_urgent": final_is_urgent, "confidence_score": final_confidence}

    def summarize_email(self, email_text: str, *, force: bool = False) -> SummarizationResponse:
        """Generates a summary for the email content using OpenRouter API."""
        if not self.api_key or not email_text:
            logger.warning("API key not available or no text to summarize. Returning empty summary.")
            return {'summary': "Summary not available."}
        
        try:
            # Similar logic to the original: avoid summarizing very short texts
            if not force and len(email_text.split()) < 20:
                logger.info("Email text too short for meaningful summarisation; returning original text.")
                return {'summary': email_text}

            # Create the prompt for summarization
            system_prompt = """
            Summarize the following email content concisely. 
            Focus on key points, actions required, and important information.
            Keep the summary under 150 words and preserve the most critical details.
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": email_text}
            ]
            
            response = self._make_openrouter_request(
                model=self.summarization_model,
                messages=messages,
                temperature=0.3,
                max_tokens=200
            )
            
            summary_text = response['choices'][0]['message']['content'].strip()
            return {'summary': summary_text}
            
        except Exception as e:
            logger.error(f"Error during email summarization: {e}")
            # Fall back to returning the original text (truncated if extremely long)
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
            snippet = email_data.get('snippet')
            if snippet is not None:
                summary = snippet[:150]  # Use snippet for non-urgent
            else:
                summary = "No summary available."

        analyzed_data: AnalyzedEmailData = {
            **email_data, # type: ignore - spread EmailData fields
            'is_urgent': urgency_result['is_urgent'],
            'summary': summary
        }
        return analyzed_data

# Example Usage:
if __name__ == '__main__':
    from datetime import datetime
    
    if "OPENROUTER_API_KEY" not in os.environ:
        print("Warning: OPENROUTER_API_KEY not set. Set this environment variable before running.")
        exit(1)
    
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
    analyzed_urgent = ai_processor.process_email(test_urgent_email)
    print(f"Email ID: {analyzed_urgent['id']}")
    print(f"Is Urgent: {analyzed_urgent['is_urgent']}")
    print(f"Summary: {analyzed_urgent['summary']}")

    logger.info("\n--- Testing Normal Email ---")
    analyzed_normal = ai_processor.process_email(test_normal_email)
    print(f"Email ID: {analyzed_normal['id']}")
    print(f"Is Urgent: {analyzed_normal['is_urgent']}")
    print(f"Summary: {analyzed_normal['summary']}") # Will be snippet for non-urgent

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
    analyzed_empty = ai_processor.process_email(empty_email)
    print(f"Email ID: {analyzed_empty['id']}")
    print(f"Is Urgent: {analyzed_empty['is_urgent']}")
    print(f"Summary: {analyzed_empty['summary']}") 