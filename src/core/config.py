import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def get_env_variable(var_name: str, default: Optional[str] = None) -> str:
    """Gets an environment variable or returns a default value.
    Raises ConfigError if the variable is not found and no default is provided.
    """
    value = os.getenv(var_name)
    if value is None:
        if default is None:
            raise ConfigError(f"Environment variable '{var_name}' not found and no default value provided.")
        return default
    return value

# Gmail API Configuration
GOOGLE_CLIENT_SECRETS_JSON_PATH: str = get_env_variable("GOOGLE_CLIENT_SECRETS_JSON_PATH")
GOOGLE_CREDENTIALS_JSON_PATH: str = get_env_variable("GOOGLE_CREDENTIALS_JSON_PATH")
GMAIL_USER_ID: str = get_env_variable("GMAIL_USER_ID", "me")
GMAIL_LABEL_URGENT: str = get_env_variable("GMAIL_LABEL_URGENT", "URGENT_AI")

# Google Cloud Pub/Sub Configuration
GOOGLE_CLOUD_PROJECT_ID: str = get_env_variable("GOOGLE_CLOUD_PROJECT_ID")
GOOGLE_PUBSUB_TOPIC_ID: str = get_env_variable("GOOGLE_PUBSUB_TOPIC_ID")
GOOGLE_PUBSUB_SUBSCRIPTION_ID: str = get_env_variable("GOOGLE_PUBSUB_SUBSCRIPTION_ID")

# Slack API Configuration
SLACK_BOT_TOKEN: str = get_env_variable("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID: str = get_env_variable("SLACK_CHANNEL_ID")

# AI Service Configuration (Optional)
OPENAI_API_KEY: Optional[str] = get_env_variable("OPENAI_API_KEY", default=None)

# Application Configuration
LOG_LEVEL: str = get_env_variable("LOG_LEVEL", "INFO").upper()

# Add a function to validate essential configurations if needed
def validate_config() -> None:
    """Validates that essential configurations are present."""
    required_vars = [
        "GOOGLE_CLIENT_SECRETS_JSON_PATH",
        "GOOGLE_CREDENTIALS_JSON_PATH",
        "GOOGLE_CLOUD_PROJECT_ID",
        "GOOGLE_PUBSUB_TOPIC_ID",
        "GOOGLE_PUBSUB_SUBSCRIPTION_ID",
        "SLACK_BOT_TOKEN",
        "SLACK_CHANNEL_ID",
    ]
    for var in required_vars:
        if not globals().get(var):
            raise ConfigError(f"Missing required configuration: {var}")

if __name__ == '__main__':
    # Example of how to use the config and validation
    try:
        validate_config()
        print("Configuration loaded and validated successfully.")
        print(f"Slack Bot Token: {SLACK_BOT_TOKEN[:5]}...") # Print a snippet for verification
    except ConfigError as e:
        print(f"Configuration Error: {e}") 