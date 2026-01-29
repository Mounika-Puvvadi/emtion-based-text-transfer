import os
import requests
import gradio as gr
import time
from dotenv import load_dotenv
from collections import deque
from threading import Lock

# Load environment variables
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

# Rate limiter
MAX_REQUESTS_PER_MINUTE = 10
MAX_REQUESTS_PER_DAY = 100
MINUTE_WINDOW = 60
DAY_WINDOW = 24 * 60 * 60

minute_timestamps = deque()
day_timestamps = deque()
rate_limit_lock = Lock()

# Page title
title = "Emotion Based Text Style Transfer"

description = """
<div style="text-align:center; max-width:650px; margin:auto;">
<p>Transform your text into any emotion or tone using AI.</p>
<p><small>Rate limit: 10/min • 100/day</small></p>
</div>
"""

# 🔥 CSS DIRECTLY IN BACKEND
custom_css = """
body {
    background: linear-gradient(135deg, #f5f7fa, #e4ebf5);
    font-family: 'Segoe UI', sans-serif;
}

.gradio-container {
    max-width: 900px !important;
    margin: auto;
}

h1 {
    text-align: center;
    color: #1f2937;
    font-weight: 600;
}

.gr-box {
    background: white !important;
    border-radius: 14px !important;
    padding: 20px !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.08);
}

label {
    font-weight: 500;
    color: #374151;
}

textarea, input {
    border-radius: 10px !important;
    border: 1px solid #d1d5db !important;
    padding: 12px !important;
    font-size: 14px !important;
}

textarea:focus, input:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    border-radius: 10px !important;
    padding: 12px !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    border: none !important;
}

button:hover {
    opacity: 0.9;
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
    return f"{tone} emotional style"

def generate_tone_variation(text, tone):
    try:
        rate_limit = is_rate_limited()
        if rate_limit:
            return rate_limit

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "Rewrite text in given tone."},
                    {"role": "user", "content": f"Tone: {tone}\nText: {text}"}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=60
        ).json()

        return response["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return str(e)

# 🌟 Gradio UI
with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown(f"# {title}")
    gr.Markdown(description)

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="Enter your text", lines=5)
            tone_input = gr.Textbox(label="Emotion / Tone", lines=1)
            generate_btn = gr.Button("Generate")

        with gr.Column():
            output = gr.Textbox(label="Modified text", lines=5, interactive=False)

    generate_btn.click(
        generate_tone_variation,
        inputs=[text_input, tone_input],
        outputs=output
    )

if __name__ == "__main__":
    demo.launch(share=True)
