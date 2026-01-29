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

# Page title and description
title = "Emotion Based Text Style Transfer"
description = f"""
<div style="text-align:center; max-width:650px; margin:auto;">
  <p>Transform your text into any tone using the OpenRouter API.</p>
  <p><small>Rate limit: {MAX_REQUESTS_PER_MINUTE}/min • {MAX_REQUESTS_PER_DAY}/day</small></p>
</div>
"""

# 🌈 LIGHT BACKGROUND CSS (EMBEDDED)
custom_css = """
body {
    background-color: #f9fafb;
    font-family: 'Segoe UI', sans-serif;
}

.gradio-container {
    max-width: 900px !important;
    margin: auto;
}

h1 {
    text-align: center;
    color: #111827;
    font-weight: 600;
}

.gr-box {
    background-color: #ffffff !important;
    border-radius: 14px !important;
    padding: 20px !important;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
}

label {
    color: #374151;
    font-weight: 500;
}

textarea, input {
    border-radius: 10px !important;
    border: 1px solid #d1d5db !important;
    padding: 12px !important;
    font-size: 14px !important;
}

textarea:focus, input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.2);
}

button {
    background-color: #3b82f6 !important;
    color: white !important;
    border-radius: 10px !important;
    padding: 12px !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    border: none !important;
}

button:hover {
    background-color: #2563eb !important;
}

.examples {
    margin-top: 20px;
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
            return "Daily limit reached. Please try again tomorrow."

        minute_timestamps.append(now)
        day_timestamps.append(now)
        return False

def get_tone_description(tone):
    predefined = {
        "playful": "fun and lighthearted",
        "serious": "formal and grave",
        "formal": "professional and proper",
        "casual": "relaxed and informal",
        "friendly": "warm and approachable"
    }
    return predefined.get(tone.lower(), f"{tone} emotional style")

def generate_tone_variation(text, tone):
    try:
        rate_limit_status = is_rate_limited()
        if rate_limit_status:
            return rate_limit_status

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "Rewrite the text in the given emotion."},
                    {"role": "user", "content": f"Emotion: {tone}\nText: {text}"}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=60
        ).json()

        return response["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Error: {str(e)}"

# 🌟 Gradio UI
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
                placeholder="e.g., happy, sad, romantic",
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
            ["I love this new cafe!", "happy"]
        ],
        inputs=[text_input, tone_input]
    )

    generate_btn.click(
        generate_tone_variation,
        inputs=[text_input, tone_input],
        outputs=output
    )

if __name__ == "__main__":
    demo.launch(share=True)
