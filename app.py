
import os
import requests
import gradio as gr
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_sop(notes, department, audience, tone):
    if not notes.strip():
        return "Please enter process notes before generating an SOP."

    if not API_KEY:
        return (
            "API key missing. Add OPENROUTER_API_KEY to your .env file."
        )

    system_prompt = """
You are an SOP documentation assistant.

Turn rough process notes into a clear draft Standard Operating Procedure.
Never invent company policies, approval limits, contact details, or facts.
If information is missing, write [CONFIRM WITH STAFF].
Do not present guesses as established company procedures.

Use exactly these sections:
1. SOP Title
2. Purpose
3. Scope
4. Prerequisites and Required Materials
5. Roles and Responsibilities
6. Numbered Procedure
7. Warnings and Risks
8. Exceptions and Escalation
9. Review Checklist
10. Missing Information Requiring Staff Confirmation

Make the procedure practical and easy for a new employee to follow.
The result is a draft and must be reviewed by authorized staff.
"""

    user_prompt = f"""
Create an SOP draft using the information below.

Department or team: {department}
Intended audience: {audience}
Writing style: {tone}

ROUGH NOTES:
{notes}

Instructions:
- Keep steps in the order provided where possible.
- Make each step specific and understandable.
- Include safety or quality warnings only when relevant.
- Clearly flag gaps instead of guessing.
- Add a checklist for reviewing the draft before approval.
"""

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "X-OpenRouter-Title": "AI SOP Builder",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 1800,
            },
            timeout=90,
        )

        if not response.ok:
            return (
                f"OpenRouter error {response.status_code}:\n\n"
                f"{response.text[:1000]}"
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except requests.Timeout:
        return "The AI request timed out. Please try again."
    except Exception as exc:
        return f"Could not generate the SOP: {str(exc)}"


with gr.Blocks(title="AI-Powered Internal SOP Builder") as demo:
    gr.Markdown(
        "# AI-Powered Internal SOP Builder\n"
        "### Convert rough process notes into a structured SOP draft."
    )

    department = gr.Textbox(
        label="Department or team",
        value="Operations",
    )

    audience = gr.Dropdown(
        label="Intended audience",
        choices=[
            "New employees",
            "Existing employees",
            "Team supervisors",
            "All staff",
        ],
        value="New employees",
    )

    tone = gr.Dropdown(
        label="Writing style",
        choices=["Simple and clear", "Formal", "Detailed"],
        value="Simple and clear",
    )

    notes = gr.Textbox(
        label="Rough process notes",
        lines=10,
        placeholder=(
            "Example: Staff receive a customer request. "
            "Check the request details. Enter the details in the system. "
            "Ask a supervisor if information is missing. "
            "Confirm completion with the customer."
        ),
    )

    generate_button = gr.Button("Generate SOP Draft", variant="primary")
    output = gr.Markdown(label="Generated SOP")

    generate_button.click(
        fn=generate_sop,
        inputs=[notes, department, audience, tone],
        outputs=output,
    )

if __name__ == "__main__":
    demo.launch()
