import smtplib
from email.message import EmailMessage
import io

import os
from dotenv import load_dotenv

# --- Load local .env if it exists ---
load_dotenv()  # will do nothing if no .env is present

# --- Get credentials from environment ---
USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")

if not USERNAME or not PASSWORD:
    raise RuntimeError("USERNAME or PASSWORD environment variable not set!")

def send_figure_email(fig):
    """
    Send a matplotlib figure as an email attachment.
    Server, port, sender, and recipient are hard-coded.
    """

    # --- Save figure to a BytesIO buffer ---
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200)
    buf.seek(0)

    recipients = ["tghughes@gmail.com", "clairetimeout@gmail.com"]
    
    # --- Build email ---
    msg = EmailMessage()
    msg["From"] = "visa@businessirelandsa.co.za"
    msg["To"] = ", ".join(recipients)  # for display in the header
    msg["Subject"] = "Weekly Visa Dashboard Chart"
    msg.set_content("Attached is this week's Visa Dashboard chart.")

    # Attach the figure
    msg.add_attachment(buf.read(),
                       maintype="image",
                       subtype="png",
                       filename="weekly_chart.png")

    # --- Send email via SMTP SSL ---
    smtp_server = "smtp.businessirelandsa.co.za"
    smtp_port = 465
    username = USERNAME
    # username = "test@test.com"
    password = PASSWORD

    with smtplib.SMTP_SSL(smtp_server, smtp_port) as s:
        s.login(username, password)
        s.send_message(msg)

    print("Email sent successfully!")
    buf.close()
    return True

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # Example usage
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    send_figure_email(fig)