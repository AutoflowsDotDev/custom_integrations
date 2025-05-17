# Email Triage Automation Architecture

## 1. System Overview

The Email Triage Automation system is designed to monitor a Gmail inbox, analyze incoming emails for urgency using an AI service, label urgent emails appropriately in Gmail, and send notifications for these urgent emails to a designated Slack channel.

## 2. Component Diagram

The system consists of three main services/modules that interact with each other and external APIs:

```mermaid
graph TD
    subgraph User Interfaces
        Gmail_UI[Gmail Inbox]
        Slack_UI[Slack Channel]
    end

    subgraph External Services
        Gmail_API[Gmail API]
        Google_PubSub[Google Cloud Pub/Sub]
        Slack_API[Slack API]
        AI_Platform[AI Platform/NLP Models (e.g., Hugging Face, OpenAI)]
    end

    subgraph Email Triage Automation System
        A[Gmail Integration Module]
        B[AI Service Module]
        C[Slack Integration Module]
        D[Configuration Manager]
        E[Main Orchestrator/Controller]
    end

    %% Data Flow & Interactions
    Gmail_UI -- New Email --> Google_PubSub
    Google_PubSub -- Push Notification --> A
    A -- Fetch Email Details --> Gmail_API
    Gmail_API -- Email Data --> A
    A -- Email Content --> E
    E -- Email for Analysis --> B
    B -- NLP Processing --> AI_Platform
    AI_Platform -- Urgency/Summary --> B
    B -- Analysis Result --> E
    
    alt Urgent Email
        E -- Label Email --> A
        A -- Apply Label --> Gmail_API
        Gmail_API -- Label Confirmation --> A
        A -- Notify Gmail_UI_Update(Label Update in Gmail)

        E -- Notification Data --> C
        C -- Send Message --> Slack_API
        Slack_API -- Message Confirmation --> C
        Slack_API -- Notify --> Slack_UI
    end

    D -.-> A
    D -.-> B
    D -.-> C
    D -.-> E

    %% Styling (Optional)
    classDef systemModule fill:#f9f,stroke:#333,stroke-width:2px;
    class A,B,C,D,E systemModule;
    classDef externalService fill:#lightgrey,stroke:#333,stroke-width:2px;
    class Gmail_API,Google_PubSub,Slack_API,AI_Platform externalService;
    classDef userInterface fill:#lightblue,stroke:#333,stroke-width:2px;
    class Gmail_UI,Slack_UI userInterface;
```

### Component Descriptions:

*   **Main Orchestrator/Controller (E):**
    *   The central component responsible for coordinating the workflow.
    *   Receives notifications of new emails (likely via the Gmail Integration Module).
    *   Passes email data to the AI Service Module for analysis.
    *   Based on the AI Service's response, instructs the Gmail Integration Module to label emails and the Slack Integration Module to send notifications.

*   **Gmail Integration Module (A):**
    *   **Responsibilities:**
        *   Authenticates with the Gmail API using OAuth 2.0.
        *   Subscribes to Google Cloud Pub/Sub for real-time notifications of new emails (preferred method) or polls the inbox periodically (fallback).
        *   Fetches full email details (headers, body) using the Gmail API when a new email is detected.
        *   Applies labels (e.g., "Urgent") to emails in Gmail as instructed by the Orchestrator.
    *   **Interfaces:** Gmail API, Google Cloud Pub/Sub, Main Orchestrator.

*   **AI Service Module (B):**
    *   **Responsibilities:**
        *   Receives email content (subject, sender, body) from the Orchestrator.
        *   Utilizes Natural Language Processing (NLP) models (either local Hugging Face `transformers` or external APIs like OpenAI) to:
            *   Determine the urgency of the email.
            *   Generate a concise summary of the email content.
        *   Returns the urgency classification and summary to the Orchestrator.
    *   **Interfaces:** AI Platform/NLP Models, Main Orchestrator.

*   **Slack Integration Module (C):**
    *   **Responsibilities:**
        *   Authenticates with the Slack API using a Bot token.
        *   Receives notification data (email subject, sender, summary) for urgent emails from the Orchestrator.
        *   Formats the data into a user-friendly message.
        *   Sends the message to the configured Slack channel via the Slack API.
    *   **Interfaces:** Slack API, Main Orchestrator.

*   **Configuration Manager (D):**
    *   **Responsibilities:**
        *   Loads and provides access to all necessary configuration parameters (API keys, tokens, label names, channel IDs, model paths, etc.).
        *   Typically loads from environment variables (e.g., via `python-dotenv` from a `.env` file) or a dedicated configuration file.
    *   **Interfaces:** All other internal modules.

### External Services:

*   **Gmail API:** Used to read emails and apply labels.
*   **Google Cloud Pub/Sub:** Provides real-time push notifications for new emails, enabling a responsive system.
*   **Slack API:** Used to send notification messages to a Slack channel.
*   **AI Platform/NLP Models:** External or local services/libraries that provide the intelligence for urgency detection and summarization.

## 3. Data Models

Key data structures used within the system:

*   **`EmailData`** (passed from Gmail Integration to AI Service):
    *   `id`: string (Gmail message ID)
    *   `subject`: string
    *   `sender`: string (email address)
    *   `body_plain`: string (plain text version of email content)
    *   `body_html`: string (HTML version of email content, optional)
    *   `received_timestamp`: datetime

*   **`AIAnalysisResult`** (passed from AI Service to Orchestrator):
    *   `email_id`: string (corresponds to `EmailData.id`)
    *   `is_urgent`: boolean
    *   `summary`: string
    *   `confidence_score`: float (optional, urgency confidence)

*   **`SlackNotificationPayload`** (passed from Orchestrator to Slack Integration):
    *   `email_subject`: string
    *   `email_sender`: string
    *   `email_summary`: string
    *   `target_channel_id`: string

## 4. API Endpoint and Data Model Documentation

(This section would be filled in as specific API endpoints are designed and implemented, especially if the system exposes its own API, e.g., for receiving Pub/Sub push notifications or manual triggering.)

*   **Incoming Pub/Sub Push Notification Endpoint (if applicable):**
    *   **Endpoint:** `/webhook/gmail` (Example)
    *   **Method:** `POST`
    *   **Payload:** Google Cloud Pub/Sub message format, containing a base64-encoded string with the Gmail `messageId` and `historyId`.
        ```json
        {
          "message": {
            "data": "BASE64_ENCODED_JSON_STRING", // e.g., {"emailAddress":"user@example.com","historyId":"12345"}
            "messageId": "PUBSUB_MESSAGE_ID",
            "publishTime": "TIMESTAMP"
          },
          "subscription": "projects/YOUR_PROJECT/subscriptions/YOUR_SUBSCRIPTION"
        }
        ```
    *   **Action:** Triggers the Main Orchestrator to fetch and process the email associated with the `messageId` (after decoding `data`).

Further API details for internal services or external interactions would be documented here as they are defined. 