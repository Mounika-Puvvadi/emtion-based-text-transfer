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

# --- Custom CSS Styling ---
custom_css = """
body {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
}

.gradio-container {
    max-width: 1000px !important;
    margin: auto !important;
    padding: 30px !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}

/* Header Styling */
h1 {
    text-align: center;
    color: #ffffff !important;
    font-size: 2.5em !important;
    margin-bottom: 10px !important;
}

/* Textbox Customization */
textarea {
    border-radius: 12px !important;
    border: 1px solid #4a90e2 !important;
    background-color: #111827 !important;
    color: #ffffff !important;
    font-size: 16px !important;
}

/* Button Styling */
button.primary-btn {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    font-size: 16px !important;
    font-weight: bold !important;
    border: none !important;
    cursor: pointer;
    transition: all 0.3s ease;
}

button.primary-btn:hover {
    transform: scale(1.03) translateY(-2px);
    box-shadow: 0 5px 15px rgba(118, 75, 162, 0.4);
}

/* Example styling */
.gr-sample-container {
    background: rgba(255, 255, 255, 0.05) !important;
    border-radius: 10px;
}

footer { visibility: hidden; }
"""

def is_rate_limited():
    with rate_limit_lock:
        now = time.time()
        while minute_timestamps and now - minute_timestamps[0] > MINUTE_WINDOW:
            minute_timestamps.popleft()
        if len(minute_timestamps) >= MAX_REQUESTS_PER_MINUTE:
            return "Rate limit exceeded. Please wait a minute before trying again."
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
        "sarcastic": "subtly humorous with a touch of irony",
        "poetic": "flowery and descriptive using metaphors"
    }
    return predefined.get(tone.lower(), f"{tone} emotional style")

def generate_tone_variation(text, tone):
    if not text or not tone:
        return "Please provide both text and a target emotion."
    
    try:
        rate_limit_status = is_rate_limited()
        if rate_limit_status:
            return rate_limit_status
        
        tone_style = get_tone_description(tone)
        system_message = f"You are expert at rewriting text in different tones. Rewrite the given text in a {tone} tone ({tone_style})."
        user_prompt = f"Rewrite the text below with the emotion '{tone}' clearly expressed:\n\nText:\n{text}"

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7
            },
            timeout=60
        ).json()

        if "error" in response:
            return f"API Error: {response['error']['message']}"

        return response['choices'][0]['message']['content'].strip()

    except Exception as e:
        return f"Error: {str(e)}"

# --- Interface Construction ---
title = "Emotion Based Text Style Transfer"
subtitle = f"Transform your text into any tone using AI. Rate-limited to {MAX_REQUESTS_PER_MINUTE} requests/min."

with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
    gr.Markdown(f"# {title}")
    gr.Markdown(f"<p style='text-align: center; color: #d1d5db;'>{subtitle}</p>")
    
    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(
                label="Enter your text",
                placeholder="Type or paste your text here...",
                lines=5
            )
            tone_input = gr.Textbox(
                label="Target Emotion / Tone",
                placeholder="e.g., happy, sarcastic, formal",
                lines=1
            )
            generate_btn = gr.Button("Generate Tone Variation", variant="primary", elem_classes=["primary-btn"])
        
        with gr.Column():
            output = gr.Textbox(
                label="Modified Result",
                lines=8,
                interactive=False
            )
    
    gr.Examples(
        examples=[
            ["I missed the bus.", "sad"],
            ["The assignment is due tomorrow.", "anxious"],
            ["I love this new cafe!", "happy"],
            ["This is so boring.", "sarcastic"]
        ],
        inputs=[text_input, tone_input]
    )
    
    generate_btn.click(
        fn=generate_tone_variation,
        inputs=[text_input, tone_input],
        outputs=output
    )

if __name__ == "__main__":
    demo.launch()
