import os
import requests
import gradio as gr
from pypdf import PdfReader
from dotenv import load_dotenv

# Local environment variables (.env file) load panrom
load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions" # Unga palaya full URL link template
# Global list history maintain panna
search_history = []

def extract_text_from_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file.name)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text
    except Exception as e:
        return f"PDF Error: {str(e)}"

def call_groq_api(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",  # 🔥 Updated to fully active latest model
        "messages": [
            {"role": "system", "content": "You are a professional AI Study Assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"BACKEND_API_ERROR_CODE_{response.status_code}: {response.text}"
    except Exception as e:
        return f"CONNECTION_CRASH_ERROR: {str(e)}"

import datetime  # ⚠️ File-oda top-la indha import irukanum

def send_to_make_webhook(summary, questions, flashcards, difficulty):
    webhook_url = "https://hook.eu1.make.com/yffwp3xjpn5acxbceivm23hwk77rlo81"  # Inga unga real Make.com link-ah paste pannunga
    
    # Unga Google Sheet headers-oda exact structural match payload:
    payload = {
        "date_and_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "difficulty_level": difficulty,
        "summary": summary,
        "questions": questions,
        "flashcards": flashcards
    }
    try:
        response = requests.post(webhook_url, json=payload)
        print(f"Webhook Sent! Status Code: {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"Webhook Error: {str(e)}")
        return None

def process_study_material(text_input, file_input, difficulty):
    global search_history
    
    final_text = ""
    if file_input is not None:
        final_text = extract_text_from_pdf(file_input)
    else:
        final_text = text_input

    if not final_text.strip():
        return "Please provide some text or upload a PDF file.", "", "", ""

    preview = final_text[:30] + "..."
    search_history.append(f"Difficulty: {difficulty} | Input: {preview}")
    history_display = "\n".join(search_history)

    # Clean structured prompt mapping
    prompt = f"""
    Analyze this text: "{final_text}"
    Difficulty Level: {difficulty}

    Provide the output strictly under these headers:
    [SUMMARY]
    Provide a concise summary here.

    [QUESTIONS]
    Provide 5 questions here.

    [FLASHCARDS]
    Provide 5 flashcards here.
    """

    ai_response = call_groq_api(prompt)

    # Dynamic parsing logic to prevent splitting errors
    summary_part = "Failed to parse Summary."
    questions_part = "Failed to parse Questions."
    flashcards_part = "Failed to parse Flashcards."

    try:
        if "[SUMMARY]" in ai_response and "[QUESTIONS]" in ai_response and "[FLASHCARDS]" in ai_response:
            summary_part = ai_response.split("[SUMMARY]")[1].split("[QUESTIONS]")[0].strip()
            questions_part = ai_response.split("[QUESTIONS]")[1].split("[FLASHCARDS]")[0].strip()
            flashcards_part = ai_response.split("[FLASHCARDS]")[1].strip()
        else:
            # Fallback format: Header check match missing aana full response blocks summary layer-la kaatum
            summary_part = ai_response
    except Exception as e:
        summary_part = f"Parsing system error: {str(e)}\n\nRaw AI Response:\n{ai_response}"

    send_to_make_webhook(summary_part, questions_part, flashcards_part, difficulty)

    return summary_part, questions_part, flashcards_part, history_display
# --- GRADIO INTERFACE SETUP ---
# --- GRADIO INTERFACE SETUP ---
# Theme ah inga irundhu remove panniyachu to fix warning
with gr.Blocks() as demo:
    gr.Markdown("# 🎓 AI Study Assistant with Automated Tracking")
    # ... (ulla irukura matha code elam apdiye irukatum)
    
    with gr.Row():
        with gr.Column(scale=1):
            text_in = gr.Textbox(label="Option A: Paste Study Notes Here", lines=6)
            file_in = gr.File(label="Option B: Or Upload Study PDF", file_types=[".pdf"])
            diff_level = gr.Radio(["Easy", "Medium", "Hard"], value="Medium", label="Select Difficulty Level")
            submit_btn = gr.Button("Generate Study Kit", variant="primary")
            
        with gr.Column(scale=2):
            sum_out = gr.Textbox(label="✨ Concise Summary", lines=5)
            q_out = gr.Textbox(label="📝 Revision Questions", lines=5)
            fc_out = gr.Textbox(label="🗂️ Generated Flashcards", lines=5)
            history_out = gr.Textbox(label="🕒 Search History Session Logs", lines=3)

    submit_btn.click(
        fn=process_study_material, 
        inputs=[text_in, file_in, diff_level], 
        outputs=[sum_out, q_out, fc_out, history_out]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)