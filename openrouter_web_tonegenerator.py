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
MINUTE_WINDOW = 60
DAY_WINDOW = 24 * 60 * 60
minute_timestamps = deque()
day_timestamps = deque()
rate_limit_lock = Lock()

# Set page title and description
title = "Emotion Based Text Style Transfer"
description = f"""
<div style="text-align: center; max-width: 650px; margin: 0 auto;">
  <div>
    <p>Transform your text into any tone using the OpenRouter API.</p>
    <p><small>Rate limit: {MAX_REQUESTS_PER_MINUTE}/min, {MAX_REQUESTS_PER_DAY}/day</small></p>
  </div>
</div>
"""

custom_css = """
body {
    background-color: #fff0f5;
    font-family: "Segoe UI", Roboto, Arial, sans-serif;
}

.gradio-container {
    max-width: 900px;
    margin: auto;
}

.gr-box {
    background: white;
    border-radius: 12px;
    box-shadow: 0 6px 16px rgba(255, 182, 193, 0.35);
}

button {
    background: #ffb6c1;
    color: #5a1a2f;
    border-radius: 8px;
    font-weight: 600;
    border: none;
}

button:hover {
    background: #ff9eb5;
}

input, textarea {
    border-radius: 8px;
    border: 1px solid #ffb6c1;
}
"""

def is_rate_limited():
    with rate_limit_lock:
        now = time.time()

        while minute_timestamps and now - minute_timestamps[0] > MINUTE_WINDOW:
            minute_timestamps.popleft()
        if len(minute_timestamps) >= MAX_REQUESTS_PER_MINUTE:
            return "Rate limit exceeded. Please wait a minute."

        while day_timestamps and now - day_timestamps[0] > DAY_WINDOW:
            day_timestamps.popleft()
        if len(day_timestamps) >= MAX_REQUESTS_PER_DAY:
            return "Daily limit reached. Try again tomorrow."

        minute_timestamps.append(now)
        day_timestamps.append(now)
        return False

def get_tone_description(tone):
    predefined = {
        "playful": "fun and lighthearted",
        "serious": "formal and grave",
        "formal": "professional and proper",
        "casual": "relaxed and informal",
        "professional": "business-appropriate",
        "friendly": "warm and approachable",
        "enthusiastic": "energetic and excited",
        "sarcastic": "humorous with irony",
        "poetic": "descriptive and metaphorical",
        "technical": "precise and accurate"
    }
    return predefined.get(tone.lower(), f"{tone} emotional style")

def generate_tone_variation(text, tone):
    try:
        rate_limit_status = is_rate_limited()
        if rate_limit_status:
            return rate_limit_status

        tone_style = get_tone_description(tone)

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": f"Rewrite text in a {tone} tone ({tone_style})."},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=60
        ).json()

        return response['choices'][0]['message']['content'].strip()

    except Exception as e:
        return f"Error: {e}"

# Gradio UI
with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown(f"# {title}")
    gr.Markdown(description)

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="Enter your text", lines=5)
            tone_input = gr.Textbox(label="Enter emotion / tone")
            generate_btn = gr.Button("Generate Tone Variation")

        with gr.Column():
            output = gr.Textbox(label="Modified text", lines=5, interactive=False)

    gr.Examples(
        examples=[
            ["I missed the bus.", "sad"],
            ["The assignment is due tomorrow.", "anxious"],
            ["I love this new cafe!", "happy"],
        ],
        inputs=[text_input, tone_input]
    )

    generate_btn.click(generate_tone_variation, [text_input, tone_input], output)

if __name__ == "__main__":
    demo.launch(share=True)
