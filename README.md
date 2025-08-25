# Recruiting Agent

This project implements a recruiting agent that assists job seekers by matching them with relevant opportunities from a job database.

## How it Works

1. A candidate sends an email to the agent's dedicated inbox.
2. The agent analyzes the candidate's profile, skills, and preferences.
3. Using a `jobs.csv` file as its database, the agent searches for suitable job openings.
4. The agent replies to the candidate with a list of matched jobs, application links, and offers further assistance like resume review or interview prep.

## Requirements

* Python 3.11 or higher
* [AgentMail API key](https://agentmail.io)
* [OpenAI API key](https://platform.openai.com)
* A publicly accessible URL for webhooks (e.g., using Ngrok).

## Setup

### 1. Configuration

Create a `.env` file in the root directory by copying the `.env.example` file. Populate it with your credentials and settings:

```sh
# .env
AGENTMAIL_API_KEY=your-agentmail-api-key
OPENAI_API_KEY=your-openai-api-key

# Inbox Configuration
INBOX_USERNAME=recruiting-agent # Or your desired AgentMail inbox username
WEBHOOK_URL=https://your-domain.ngrok-free.app # Your public webhook URL

```

### 2. Job Data

Ensure you have a `jobs.csv` file in the root directory with the job listings you want the agent to use. The CSV should include columns like `job_title`, `job_location`, and `job_url`.

### 3. Installation

Create a virtual environment and install the required packages.

```sh
# Using venv
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

## Running the Agent

1. **Start the server:**
    Run the main application file. This will start a Flask server to listen for incoming email webhooks.

    ```sh
    python main.py
    ```

2. **Expose your local server (if running locally):**
    If you are running the server on your local machine, use a tool like Ngrok to create a public URL that forwards to your local port (e.g., port 5000).

    ```sh
    ngrok http 5000
    ```

    Update the `WEBHOOK_URL` in your `.env` file with the URL provided by Ngrok.

3. **Test the Agent:**
    Send an email to your configured agent inbox (e.g., `recruiting-agent@agentmail.to`). Introduce yourself as a job seeker and describe your skills and career interests. The agent should reply with relevant job opportunities from your `jobs.csv` file.