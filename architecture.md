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

Key data structures used within the system internally. For API request/response models, see the section below.

*   **`EmailDataInternal`** (passed from Gmail Integration to AI Service):
    *   `id`: string (Gmail message ID)
    *   `subject`: string
    *   `sender`: string (email address)
    *   `body_plain`: string (plain text version of email content)
    *   `body_html`: string (HTML version of email content, optional)
    *   `received_timestamp`: datetime

*   **`AIAnalysisResultInternal`** (passed from AI Service to Orchestrator):
    *   `email_id`: string (corresponds to `EmailDataInternal.id`)
    *   `is_urgent`: boolean
    *   `summary`: string
    *   `confidence_score`: float (optional, urgency confidence)

*   **`SlackNotificationPayloadInternal`** (passed from Orchestrator to Slack Integration):
    *   `email_subject`: string
    *   `email_sender`: string
    *   `email_summary`: string
    *   `target_channel_id`: string

## 4. API Endpoint and Data Model Documentation

The system exposes several API endpoints for health checks, metrics, and core email processing functionalities. All endpoints are prefixed with `/api/v1` (not shown in the paths below for brevity but implied by the application setup).

### 4.1. Health Check

*   **Endpoint:** `/health`
*   **Method:** `GET`
*   **Description:** Checks the health of the service and its dependencies (system resources, Gmail, AI, Slack).
*   **Request:** None
*   **Response (`ServiceHealthResponse`):**
    ```json
    {
      "status": "string (OK, DEGRADED, UNAVAILABLE)",
      "uptime": "float (seconds)",
      "version": "string",
      "services": {
        "system": "string (OK, DEGRADED, UNAVAILABLE)",
        "gmail": "string (OK, DEGRADED, UNAVAILABLE)",
        "ai": "string (OK, DEGRADED, UNAVAILABLE)",
        "slack": "string (OK, DEGRADED, UNAVAILABLE)"
      },
      "message": "string (e.g., Running on Linux ...) "
    }
    ```

### 4.2. Metrics

*   **Endpoint:** `/metrics`
*   **Method:** `GET`
*   **Description:** Provides Prometheus-compatible metrics for monitoring application performance and behavior.
*   **Request:** None
*   **Response:** Text-based Prometheus metrics format.
    ```
    # HELP emails_processed_total Total number of emails processed
    # TYPE emails_processed_total counter
    emails_processed_total{is_urgent="true",status="success"} 1.0
    # ... (other metrics)
    ```

### 4.3. Webhook for Gmail Pub/Sub

*   **Endpoint:** `/webhook/pubsub`
*   **Method:** `POST`
*   **Description:** Receives push notifications from Google Cloud Pub/Sub when changes occur in the watched Gmail mailbox (e.g., new email arrival). It extracts the `historyId` and triggers email processing.
*   **Request Payload (Google Cloud Pub/Sub message format):**
    ```json
    {
      "message": {
        "data": "BASE64_ENCODED_JSON_STRING", // e.g., {"emailAddress":"user@example.com","historyId":"12345"}
        "messageId": "string (Pub/Sub Message ID)",
        "publishTime": "string (Timestamp)"
      },
      "subscription": "string (e.g., projects/YOUR_PROJECT/subscriptions/YOUR_SUBSCRIPTION)"
    }
    ```
*   **Action:** Parses the notification, extracts `historyId`, and initiates processing of new emails based on that history ID (internally calls logic similar to `/emails/history`).
*   **Response (on success, `202 Accepted`):**
    ```json
    {
      "status": "success",
      "message": "PubSub notification processed successfully"
    }
    ```
*   **Error Responses:** Standard HTTP error codes (e.g., 400 for bad request, 500 for server error) with a JSON detail message.

### 4.4. Process Single Email

*   **Endpoint:** `/emails/process`
*   **Method:** `POST`
*   **Description:** Manually triggers the processing of a single email given its Gmail message ID.
*   **Request Payload (`EmailProcessRequest`):**
    ```json
    {
      "email_id": "string (Gmail message ID)"
    }
    ```
*   **Action:** Fetches the specified email, analyzes it for urgency, applies a label if urgent, and sends a Slack notification if urgent.
*   **Response (`EmailProcessResponse`, on success `202 Accepted`):
    ```json
    {
      "success": true,
      "email_id": "string (Gmail message ID)",
      "is_urgent": true, // or false
      "message": "string (e.g., Email processed successfully in X.XX seconds)"
    }
    ```
    If email not found or other issues:
    ```json
    {
      "success": false,
      "email_id": "string (Gmail message ID)",
      "message": "string (Error message, e.g., Email not found or could not be retrieved)"
    }
    ```
*   **Error Responses:** Standard HTTP error codes (e.g., 503 for service unavailability, 500 for internal server error) with a JSON detail message.

### 4.5. Process Gmail History

*   **Endpoint:** `/emails/history`
*   **Method:** `POST`
*   **Description:** Manually triggers the processing of new emails based on a Gmail `historyId`. This is typically used by the Pub/Sub webhook but can be called directly.
*   **Request Payload (`ProcessHistoryRequest`):
    ```json
    {
      "history_id": "string (Gmail history ID)"
    }
    ```
*   **Action:** Fetches Gmail history records starting from the given `historyId`, identifies new messages, and processes each one (fetches, analyzes, labels, notifies as appropriate).
*   **Response (`ProcessHistoryResponse`, on success `202 Accepted`):
    ```json
    {
      "success": true,
      "history_id": "string (Gmail history ID)",
      "processed_emails": 0, // integer, number of emails processed from this history update
      "message": "string (e.g., Processed X emails from history update)"
    }
    ```
*   **Error Responses:** Standard HTTP error codes (e.g., 503 for service unavailability, 500 for internal server error) with a JSON detail message.

Further API details for internal services or external interactions would be documented here as they are defined. 