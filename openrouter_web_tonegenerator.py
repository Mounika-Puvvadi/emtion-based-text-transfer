import os
import requests
import gradio as gr
import time
from dotenv import load_dotenv
from collections import deque
from threading import Lock

# Load environment variables from .env file
load_dotenv()

# OpenRouter API configuration
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
    "HTTP-Referer": "https://github.com/your-username/your-repo",
    "X-Title": "OpenRouter Tone Generator",
    "Content-Type": "application/json"
}
MODEL = "arcee-ai/trinity-large-preview:free"

# Rate limiter settings
MAX_REQUESTS_PER_MINUTE = 10
MAX_REQUESTS_PER_DAY = 100
MINUTE_WINDOW = 60  # seconds
DAY_WINDOW = 24 * 60 * 60  # seconds
minute_timestamps = deque()
day_timestamps = deque()
rate_limit_lock = Lock()

# Set page title and description
title = "Emotion Based Text Style Transfer"
description = f"""
<div style="text-align: center; max-width: 650px; margin: 0 auto;">
  <div>
    <p>Transform your text into any tone using the OpenRouter API. Type any emotion or tone and paste your text to get started!</p>
    <p><small>This service is rate-limited to {MAX_REQUESTS_PER_MINUTE} requests per minute and {MAX_REQUESTS_PER_DAY} requests per day.</small></p>
  </div>
</div>
"""
custom_css = """
body {
    background-color: #fdecef;
}
"""

def is_rate_limited():
    with rate_limit_lock:
        now = time.time()
        
        # Check minute limit
        while minute_timestamps and now - minute_timestamps[0] > MINUTE_WINDOW:
            minute_timestamps.popleft()
        if len(minute_timestamps) >= MAX_REQUESTS_PER_MINUTE:
            return "Rate limit exceeded. Please wait a minute before trying again."
        
        # Check daily limit
        while day_timestamps and now - day_timestamps[0] > DAY_WINDOW:
            day_timestamps.popleft()
        if len(day_timestamps) >= MAX_REQUESTS_PER_DAY:
            return "Daily limit reached. Please try again tomorrow."
        
        minute_timestamps.append(now)
        day_timestamps.append(now)
        return False

def get_tone_description(tone):
    predefined = {
        "playful": "fun and lighthearted, using casual language and maybe even some wordplay",
        "serious": "formal and grave, emphasizing importance and gravity",
        "formal": "professional and proper, using business etiquette and formal vocabulary",
        "casual": "relaxed and informal, like talking to a friend",
        "professional": "business-appropriate, maintaining clarity and professionalism",
        "friendly": "warm and approachable, like chatting with a close friend",
        "enthusiastic": "energetic and excited, using upbeat language and positive expressions",
        "sarcastic": "subtly humorous with a touch of irony and wit",
        "poetic": "flowery and descriptive, using metaphors and vivid language",
        "technical": "precise and technical, focusing on accuracy and specificity"
    }
    return predefined.get(tone.lower(), f"{tone} emotional style")

def generate_tone_variation(text, tone):
    try:
        rate_limit_status = is_rate_limited()
        if rate_limit_status:
            return rate_limit_status
        
        tone_style = get_tone_description(tone)

        system_message = f"""You are expert at rewriting text in different tones.
Your task is to rewrite the given text in a {tone} tone ({tone_style})."""

        user_prompt = f"""Rewrite the text below with the emotion '{tone}' clearly expressed:
Text:
{text}"""

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=60
        ).json()

        if "error" in response:
            return f"API Error: {response['error']['message']}"

        return response['choices'][0]['message']['content'].strip()

    except Exception as e:
        return f"Error: {str(e)}"

# Create the Gradio interface
with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown(f"# {title}")
    gr.Markdown(description)
    
    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(
                label="Enter your text",
                placeholder="Type or paste your text here...",
                lines=5
            )
            tone_input = gr.Textbox(
                label="Enter emotion / tone",
                placeholder="e.g., happy, sad, romantic, angry, formal, relaxed",
                lines=1
            )
            generate_btn = gr.Button("Generate Tone Variation")
        
        with gr.Column():
            output = gr.Textbox(
                label="Modified text",
                lines=5,
                interactive=False
            )
    
    gr.Examples(
        examples=[
            ["I missed the bus.", "sad"],
            ["The assignment is due tomorrow.", "anxious"],
            ["I love this new cafe!", "happy"],
            ["This is so boring.", "sarcastic"],
            ["Let’s celebrate your success!", "joyful"],
            ["Explain this seriously:", "serious"]
        ],
        inputs=[text_input, tone_input]
    )
    
    generate_btn.click(
        fn=generate_tone_variation,
        inputs=[text_input, tone_input],
        outputs=output
    )

# Launch the app
if __name__ == "__main__":
    demo.launch(share=True)
