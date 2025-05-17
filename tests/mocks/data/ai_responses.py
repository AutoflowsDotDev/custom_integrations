"""
Mock AI API responses for testing.
This file contains synthetic responses from the AI service covering various scenarios.
"""
from typing import Dict, List, Any

# Standard urgency classification responses
URGENT_CLASSIFICATION_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": '{"classification": "URGENT", "confidence": 0.92}'
            },
            "index": 0
        }
    ],
    "id": "chatcmpl-abc123",
    "created": 1686123456,
    "model": "openai/gpt-3.5-turbo",
    "usage": {
        "prompt_tokens": 157,
        "completion_tokens": 23,
        "total_tokens": 180
    }
}

NON_URGENT_CLASSIFICATION_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": '{"classification": "NOT_URGENT", "confidence": 0.87}'
            },
            "index": 0
        }
    ],
    "id": "chatcmpl-def456",
    "created": 1686123457,
    "model": "openai/gpt-3.5-turbo",
    "usage": {
        "prompt_tokens": 142,
        "completion_tokens": 25,
        "total_tokens": 167
    }
}

# Classification with low confidence (borderline case)
LOW_CONFIDENCE_CLASSIFICATION_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": '{"classification": "NOT_URGENT", "confidence": 0.51}'
            },
            "index": 0
        }
    ],
    "id": "chatcmpl-ghi789",
    "created": 1686123458,
    "model": "openai/gpt-3.5-turbo",
    "usage": {
        "prompt_tokens": 165,
        "completion_tokens": 25,
        "total_tokens": 190
    }
}

# Edge case: Non-JSON response format for urgency
MALFORMED_URGENCY_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "Based on my analysis, this email is URGENT and requires immediate attention."
            },
            "index": 0
        }
    ],
    "id": "chatcmpl-jkl012",
    "created": 1686123459,
    "model": "openai/gpt-3.5-turbo",
    "usage": {
        "prompt_tokens": 150,
        "completion_tokens": 17,
        "total_tokens": 167
    }
}

# Edge case: Partial or incomplete JSON in response
PARTIAL_JSON_URGENCY_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "The email classification is: {'classification': 'URGENT'"
            },
            "index": 0
        }
    ],
    "id": "chatcmpl-mno345",
    "created": 1686123460,
    "model": "openai/gpt-3.5-turbo",
    "usage": {
        "prompt_tokens": 155,
        "completion_tokens": 13,
        "total_tokens": 168
    }
}

# Standard summarization responses for various email types
STANDARD_SUMMARY_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "Weekly project update confirming all deliverables are on track. No immediate action required."
            },
            "index": 0
        }
    ],
    "id": "chatcmpl-pqr678",
    "created": 1686123461,
    "model": "openai/gpt-3.5-turbo",
    "usage": {
        "prompt_tokens": 350,
        "completion_tokens": 18,
        "total_tokens": 368
    }
}

URGENT_SUMMARY_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "ALERT: Production server is down affecting all customer transactions. Immediate investigation required to restore service. This is a high-priority issue that needs immediate resolution."
            },
            "index": 0
        }
    ],
    "id": "chatcmpl-stu901",
    "created": 1686123462,
    "model": "openai/gpt-3.5-turbo",
    "usage": {
        "prompt_tokens": 320,
        "completion_tokens": 29,
        "total_tokens": 349
    }
}

# Edge case: Very short summary
SHORT_SUMMARY_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "Server down. Fix needed."
            },
            "index": 0
        }
    ],
    "id": "chatcmpl-vwx234",
    "created": 1686123463,
    "model": "openai/gpt-3.5-turbo",
    "usage": {
        "prompt_tokens": 280,
        "completion_tokens": 6,
        "total_tokens": 286
    }
}

# Edge case: Very long summary
LONG_SUMMARY_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "This email contains an extremely detailed description of project requirements spanning multiple areas. " + 
                           "The sender outlines specifications for the new system architecture, database design, front-end user interface, " +
                           "backend processing, security considerations, performance benchmarks, testing strategies, deployment plans, " +
                           "maintenance schedules, user training, documentation standards, hardware requirements, software dependencies, " +
                           "compliance matters, budget considerations, timeline milestones, team responsibilities, risk assessment, " +
                           "quality assurance protocols, contingency planning, integration points with existing systems, " +
                           "and future scalability. The document serves as a comprehensive reference for the entire project scope and should be " +
                           "reviewed carefully by the development team to ensure all requirements are properly addressed in the implementation phase."
            },
            "index": 0
        }
    ],
    "id": "chatcmpl-yz7890",
    "created": 1686123464,
    "model": "openai/gpt-3.5-turbo",
    "usage": {
        "prompt_tokens": 800,
        "completion_tokens": 147,
        "total_tokens": 947
    }
}

# Edge case: Summary with special characters and multilingual content
SPECIAL_CHARS_SUMMARY_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "Email contains multiple languages: French (éèêëàçñ), Chinese (你好), Japanese (こんにちは), and Korean (안녕하세요). Special characters are being used for testing internationalization support."
            },
            "index": 0
        }
    ],
    "id": "chatcmpl-123abc",
    "created": 1686123465,
    "model": "openai/gpt-3.5-turbo",
    "usage": {
        "prompt_tokens": 300,
        "completion_tokens": 32,
        "total_tokens": 332
    }
}

# Edge case: Summary with HTML entities (should be properly escaped in actual usage)
HTML_SUMMARY_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "Email uses HTML formatting with <strong>bold text</strong> and <a href='http://example.com'>links</a>. The content should be properly sanitized before display."
            },
            "index": 0
        }
    ],
    "id": "chatcmpl-456def",
    "created": 1686123466,
    "model": "openai/gpt-3.5-turbo",
    "usage": {
        "prompt_tokens": 290,
        "completion_tokens": 28,
        "total_tokens": 318
    }
}

# Error responses
API_ERROR_RESPONSE = {
    "error": {
        "message": "The API key provided is invalid or has expired.",
        "type": "invalid_request_error",
        "param": None,
        "code": "invalid_api_key"
    }
}

RATE_LIMIT_ERROR_RESPONSE = {
    "error": {
        "message": "Rate limit exceeded. Please try again later.",
        "type": "rate_limit_error",
        "param": None,
        "code": "rate_limit_exceeded"
    }
}

MODEL_OVERLOADED_ERROR_RESPONSE = {
    "error": {
        "message": "The model is currently overloaded. Please try again later.",
        "type": "server_error",
        "param": None,
        "code": "model_overloaded"
    }
}

# Collect all responses by category for easy access
URGENCY_RESPONSES = {
    'urgent': URGENT_CLASSIFICATION_RESPONSE,
    'non_urgent': NON_URGENT_CLASSIFICATION_RESPONSE,
    'low_confidence': LOW_CONFIDENCE_CLASSIFICATION_RESPONSE,
    'malformed': MALFORMED_URGENCY_RESPONSE,
    'partial_json': PARTIAL_JSON_URGENCY_RESPONSE
}

SUMMARY_RESPONSES = {
    'standard': STANDARD_SUMMARY_RESPONSE,
    'urgent': URGENT_SUMMARY_RESPONSE,
    'short': SHORT_SUMMARY_RESPONSE,
    'long': LONG_SUMMARY_RESPONSE,
    'special_chars': SPECIAL_CHARS_SUMMARY_RESPONSE,
    'html': HTML_SUMMARY_RESPONSE
}

ERROR_RESPONSES = {
    'api_error': API_ERROR_RESPONSE,
    'rate_limit': RATE_LIMIT_ERROR_RESPONSE,
    'model_overloaded': MODEL_OVERLOADED_ERROR_RESPONSE
}

# Export for easy import in tests
__all__ = [
    'URGENT_CLASSIFICATION_RESPONSE',
    'NON_URGENT_CLASSIFICATION_RESPONSE',
    'LOW_CONFIDENCE_CLASSIFICATION_RESPONSE',
    'MALFORMED_URGENCY_RESPONSE',
    'PARTIAL_JSON_URGENCY_RESPONSE',
    'STANDARD_SUMMARY_RESPONSE',
    'URGENT_SUMMARY_RESPONSE',
    'SHORT_SUMMARY_RESPONSE',
    'LONG_SUMMARY_RESPONSE',
    'SPECIAL_CHARS_SUMMARY_RESPONSE',
    'HTML_SUMMARY_RESPONSE',
    'API_ERROR_RESPONSE',
    'RATE_LIMIT_ERROR_RESPONSE',
    'MODEL_OVERLOADED_ERROR_RESPONSE',
    'URGENCY_RESPONSES',
    'SUMMARY_RESPONSES',
    'ERROR_RESPONSES'
] 