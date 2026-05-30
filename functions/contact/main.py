import functions_framework
import json
import os
import re
import urllib.request


def send_owner_email(name, email, message):
    import sendgrid
    from sendgrid.helpers.mail import Mail

    api_key = os.environ.get("SENDGRID_API_KEY", "")
    if not api_key:
        print("SENDGRID_API_KEY not set — skipping owner email")
        return

    to_email = os.environ.get("CONTACT_EMAIL", "leedulcio@gorillac.net")
    body = f"Name:    {name}\nEmail:   {email}\n\nMessage:\n{message}"

    sg = sendgrid.SendGridAPIClient(api_key)
    mail = Mail(
        from_email="noreply@gorillac.net",
        to_emails=to_email,
        subject=f"gorillac.net — New lead from {name}",
        plain_text_content=body,
    )
    sg.send(mail)


def send_welcome_email(name, email):
    import sendgrid
    from sendgrid.helpers.mail import Mail

    api_key = os.environ.get("SENDGRID_API_KEY", "")
    if not api_key:
        return

    body = (
        f"Hi {name},\n\n"
        "Thanks for reaching out to GorillaC! We've received your message and will be in touch within 1 business day.\n\n"
        "In the meantime, feel free to learn more about our services at https://gorillac.net.\n\n"
        "— Lee Dulcio\n"
        "GorillaC | leedulcio@gorillac.net"
    )

    sg = sendgrid.SendGridAPIClient(api_key)
    mail = Mail(
        from_email="noreply@gorillac.net",
        to_emails=email,
        subject="We got your message — GorillaC",
        plain_text_content=body,
    )
    sg.send(mail)


def post_to_platform(name, email, message, service=None):
    platform_url = os.environ.get("PLATFORM_API_URL", "")
    api_key = os.environ.get("PLATFORM_INBOUND_KEY", "")
    if not platform_url or not api_key:
        print("PLATFORM_API_URL or PLATFORM_INBOUND_KEY not set — skipping CRM post")
        return

    body = {"full_name": name, "email": email, "message": message}
    if service:
        body["service"] = service

    payload = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(
        f"{platform_url.rstrip('/')}/api/leads/inbound",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"Lead posted to platform: {resp.status}")
    except Exception as exc:
        print(f"Platform post failed (non-fatal): {exc}")


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
    service = str(data.get("service", "")).strip() or None

    if not (name and email and message):
        return (json.dumps({"error": "All fields are required."}), 400, headers)

    if len(name) > 255:
        return (json.dumps({"error": "Name is too long."}), 400, headers)
    if len(email) > 255 or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return (json.dumps({"error": "Invalid email address."}), 400, headers)
    if len(message) > 5000:
        return (json.dumps({"error": "Message too long."}), 400, headers)

    try:
        send_owner_email(name, email, message)
    except Exception as exc:
        print(f"Owner email error: {exc}")
        return (json.dumps({"error": "Failed to send message. Please try again."}), 500, headers)

    post_to_platform(name, email, message, service=service)

    try:
        send_welcome_email(name, email)
    except Exception as exc:
        print(f"Welcome email error (non-fatal): {exc}")

    return (json.dumps({"success": True}), 200, headers)
