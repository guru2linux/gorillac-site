import functions_framework
import json
import os
import re


def send_email(name, email, message):
    import sendgrid
    from sendgrid.helpers.mail import Mail

    api_key = os.environ.get("SENDGRID_API_KEY", "")
    if not api_key:
        print("SENDGRID_API_KEY not set — skipping email")
        return

    to_email = os.environ.get("CONTACT_EMAIL", "leedulcio@gorillac.net")
    body = f"Name:    {name}\nEmail:   {email}\n\nMessage:\n{message}"

    sg = sendgrid.SendGridAPIClient(api_key)
    mail = Mail(
        from_email="noreply@gorillac.net",
        to_emails=to_email,
        subject=f"gorillac.net — Contact from {name}",
        plain_text_content=body,
    )
    sg.send(mail)


def cors_headers():
    return {
        "Access-Control-Allow-Origin": "https://gorillac.net",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json",
    }


@functions_framework.http
def contact_handler(request):
    headers = cors_headers()

    if request.method == "OPTIONS":
        return ("", 204, headers)

    if request.method != "POST":
        return (json.dumps({"error": "Method not allowed"}), 405, headers)

    data = request.get_json(silent=True) or {}
    name    = str(data.get("name", "")).strip()
    email   = str(data.get("email", "")).strip()
    message = str(data.get("message", "")).strip()

    if not (name and email and message):
        return (json.dumps({"error": "All fields are required."}), 400, headers)

    if len(name) > 255:
        return (json.dumps({"error": "Name is too long."}), 400, headers)
    if len(email) > 255 or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return (json.dumps({"error": "Invalid email address."}), 400, headers)
    if len(message) > 5000:
        return (json.dumps({"error": "Message too long."}), 400, headers)

    try:
        send_email(name, email, message)
    except Exception as exc:
        print(f"Email error: {exc}")
        return (json.dumps({"error": "Failed to send message. Please try again."}), 500, headers)

    return (json.dumps({"success": True}), 200, headers)
