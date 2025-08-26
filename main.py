from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
from threading import Thread
import uuid

import ngrok
from flask import Flask, request, Response

from agentmail import AgentMail
from agentmail_toolkit.openai import AgentMailToolkit
from agents import WebSearchTool, Agent, Runner
from job_search_tool import search_jobs, get_job_categories, get_recent_jobs

# Configuration
port = int(os.getenv("PORT", 8080))
username = os.getenv("INBOX_USERNAME")
inbox = f"{username}@agentmail.to"
domain = os.getenv("WEBHOOK_DOMAIN")

# Environment validation
if not username:
    print("⚠️  WARNING: INBOX_USERNAME is not set!")
    print("   Make sure your .env file contains: INBOX_USERNAME=recruiting-test")

if not os.getenv("AGENTMAIL_API_KEY"):
    print("⚠️  WARNING: AGENTMAIL_API_KEY is not set!")
    print("   Add your AgentMail API key to the .env file")

client_id = "recruiting-agent-1"

# Initialize services
listener = ngrok.forward(port, domain=domain, authtoken_from_env=True)
app = Flask(__name__)

client = AgentMail(api_key=os.getenv("AGENTMAIL_API_KEY"))

# Create inbox and webhook
inbox_obj = client.inboxes.create(username=username, client_id=client_id) 
inbox_address = f"{username}@agentmail.to"

webhook_url = f"{listener.url()}/webhooks"

client.webhooks.create(
    url=webhook_url,
    inbox_ids=[inbox_obj.inbox_id],
    event_types=["message.received"],
    client_id="recruiting-agent-webhook",
)

# Load system prompt - try file first, then environment variable
try:
    with open("system_prompt.txt", "r") as f:
        system_prompt = f.read()
    instructions = system_prompt.strip().replace("{inbox}", inbox_address)
    print("📄 System prompt loaded from system_prompt.txt")
except FileNotFoundError:
    system_prompt = os.getenv("RECRUITING_SYSTEM_PROMPT")
    if system_prompt:
        instructions = system_prompt.strip().replace("{inbox}", inbox_address)
        print("🌐 System prompt loaded from environment variable")
    else:
        print("⚠️  WARNING: No system_prompt.txt file found and RECRUITING_SYSTEM_PROMPT environment variable not set!")
        # Fallback to a basic prompt
        instructions = f"You are a recruiting agent for {inbox_address}. Help candidates find jobs from our database using the search_jobs tool."

# Initialize agent
agent = Agent( 
    name="Recruiting Agent",
    instructions=instructions,
    tools=AgentMailToolkit(client).get_tools() + [WebSearchTool(), search_jobs, get_job_categories, get_recent_jobs],
)

@app.route("/", methods=["POST"]) 
def receive_webhook_root():
    """Handle webhooks at root endpoint."""
    print("📨 WEBHOOK received at ROOT /")
    print(request.json)
    Thread(target=process_webhook, args=(request.json,)).start()
    return Response(status=200)

@app.route("/webhooks", methods=["POST"])
def receive_webhook():
    """Handle webhooks at /webhooks endpoint."""
    print("📨 WEBHOOK received at /webhooks")
    print(request.json)
    Thread(target=process_webhook, args=(request.json,)).start()
    return Response(status=200)

@app.route("/", methods=["GET"])
def root_get():
    """Health check endpoint."""
    return Response("Recruiting Agent Webhook Endpoint", status=200)


def process_webhook(payload):
    """Process incoming email webhook and generate agent response.
    
    Args:
        payload: Webhook payload containing email data
    """
    try:
        email = payload["message"]
        thread_id = email.get("thread_id")
        
        if not thread_id:
            print("⚠️  No thread_id found in email payload")
            return
        
        print(f"Processing email from: {email.get('from', 'Unknown')}")
        
        # Fetch full thread context for conversation continuity
        thread_context = []
        try:
            thread = client.inboxes.threads.get(inbox_id=inbox_obj.inbox_id, thread_id=thread_id)
            print(f"🔍 DEBUG: Fetched thread {thread_id} with {len(thread.messages)} messages")
            
            # Build conversation context from thread history
            for msg in thread.messages:
                message_content = msg.text or msg.html or "No content"
                
                # Check if this message is from an external sender (user) or our agent (assistant)
                if hasattr(msg, 'from_') and msg.from_ and not msg.from_.endswith('@agentmail.to'):
                    thread_context.append({"role": "user", "content": message_content})
                else:
                    thread_context.append({"role": "assistant", "content": message_content})
            
            print(f"🔍 DEBUG: Thread context has {len(thread_context)} messages")
            
        except Exception as e:
            print(f"⚠️  Error fetching thread {thread_id}: {e}")
            thread_context = []
        
        # Include attachment info if present
        attachments_info = ""
        if email.get("attachments"):
            attachments_info = "\nAttachments:\n"
            for att in email["attachments"]:
                attachments_info += f"- {att['filename']} (ID: {att['attachment_id']}, Type: {att['content_type']}, Size: {att['size']} bytes)\n"
        
        # Construct prompt with email details and tool instructions
        prompt = f"""
From: {email["from"]}
Subject: {email["subject"]}
Body:\n{email["text"]}
{attachments_info}

IMPORTANT FOR TOOL CALLS:
- THREAD_ID: {email.get("thread_id", "N/A")}
- MESSAGE_ID: {email.get("message_id", "N/A")}

Use these EXACT values when calling get_thread and get_attachment tools.

FORMATTING REQUIREMENTS:
- Use HTML formatting in your response (this will be sent as an HTML email)
- For bold text: use <strong>text</strong> instead of **text**
- For job listings: use clean HTML structure with <p>, <strong>, <em> tags
- For links: use <a href="url">text</a> format
- No markdown syntax (**, *, etc.) - only HTML tags
"""
        
        # Run agent with full conversation context
        response = asyncio.run(Runner.run(agent, thread_context + [{"role": "user", "content": prompt}]))
        
        print(f"Response: {response.final_output[:100]}...") if len(response.final_output) > 100 else print(f"Response: {response.final_output}")
        
        # Send reply
        client.inboxes.messages.reply(
            inbox_id=inbox_obj.inbox_id,
            message_id=email["message_id"],
            html=response.final_output,
        )
        
        
    except KeyError as e:
        print(f"❌ Missing required field in webhook payload: {e}")
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        # Optionally send error response to user
        try:
            error_response = "I'm experiencing technical difficulties. Please try again later."
            client.inboxes.messages.reply(
                inbox_id=inbox_obj.inbox_id,
                message_id=payload.get("message", {}).get("message_id"),
                html=error_response,
            )
        except:
            print("❌ Failed to send error response")


if __name__ == "__main__":
    print(f"Inbox: {inbox_address}\n")
    print(f"Starting server on port {port}")
    
    app.run(host="0.0.0.0", port=port)
