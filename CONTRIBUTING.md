# Contributing to Email Triage Automation

Thank you for considering contributing to the Email Triage Automation project! We welcome contributions from the community.

## Development Setup

To set up your development environment, please follow these steps:

1.  **Fork the Repository:** Start by forking the main repository to your own GitHub account.
2.  **Clone Your Fork:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/email-triage-automation.git
    cd email-triage-automation
    ```
3.  **Create a Virtual Environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```
4.  **Install Dependencies:** Install the project dependencies, including development tools.
    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt  # (If a separate dev requirements file exists)
    ```
5.  **Set Up Pre-commit Hooks (Optional but Recommended):** If the project uses pre-commit hooks for linting and formatting, install them:
    ```bash
    pre-commit install
    ```
6.  **Configure Environment Variables:**
    *   Copy the example environment file (e.g., `.env.example`) to `.env`.
        ```bash
        cp .env.example .env
        ```
    *   Fill in the necessary API keys, tokens, and configuration details in your local `.env` file for Gmail, Google Cloud, and Slack. **Do not commit your `.env` file.**

7.  **Run Tests:** Ensure all tests pass before you start making changes.
    ```bash
    pytest  # Or the project's specific test command
    ```

## Making Changes

1.  **Create a New Branch:** Create a descriptive branch for your feature or bug fix.
    ```bash
    git checkout -b feature/your-feature-name
    # or
    git checkout -b fix/your-bug-fix-name
    ```
2.  **Write Code:** Make your changes, adhering to the project's coding style and guidelines.
3.  **Write Tests:** Add unit tests and integration tests for any new functionality or bug fixes.
4.  **Ensure Tests Pass:** Run all tests to confirm your changes haven't broken existing functionality.
5.  **Lint and Format:** Ensure your code is well-formatted and passes linting checks.
    ```bash
    # (Commands for linters like Flake8, Black, isort, etc., if applicable)
    # If using pre-commit, it will handle this automatically on commit.
    ```
6.  **Commit Your Changes:** Write clear and concise commit messages.
    ```bash
    git add .
    git commit -m "feat: Briefly describe your feature"
    # or
    git commit -m "fix: Briefly describe your bug fix"
    ```
7.  **Push to Your Fork:**
    ```bash
    git push origin feature/your-feature-name
    ```

## Submitting a Pull Request

1.  Open a pull request (PR) from your fork's branch to the `main` branch (or the appropriate development branch) of the original repository.
2.  Provide a clear title and description for your PR, explaining the changes and referencing any relevant issues.
3.  Ensure your PR passes all automated checks (CI/CD pipeline).
4.  Be prepared to address any feedback or requested changes from the maintainers.

## Coding Guidelines

*   Follow PEP 8 for Python code.
*   Write clear, maintainable, and well-documented code.
*   Include docstrings for modules, classes, and functions.
*   Keep your changes focused on the specific feature or bug fix.

Thank you for contributing! 